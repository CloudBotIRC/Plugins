from cloudbot import hook
from cloudbot.util import timeformat, botvars

import time
import re

CAN_DOWNVOTE = False

from sqlalchemy import Table, Column, Integer, Float, String, PrimaryKeyConstraint
from sqlalchemy import select

karma_table = Table(
    'karma',
    botvars.metadata,
    Column('nick_vote', String),
    Column('up_karma', Integer, default=0),
    Column('down_karma', Integer, default=0),
    Column('total_karma', Integer, default=0),
    PrimaryKeyConstraint('nick_vote')
)

voter_table = Table(
    'karma_voters',
    botvars.metadata,
    Column('voter', String),
    Column('votee', String),
    Column('epoch', Float),
    PrimaryKeyConstraint('voter', 'votee')
)


def up(db, nick_vote):
    db.execute("""UPDATE karma SET
               up_karma = up_karma + 1,
               total_karma = total_karma + 1 WHERE nick_vote=?""", (nick_vote.lower(),))
    db.commit()


def down(db, nick_vote):
    db.execute("""UPDATE karma SET
               down_karma = down_karma + 1,
               total_karma = total_karma + 1 WHERE nick_vote=?""", (nick_vote.lower(),))
    db.commit()


def allowed(db, nick, nick_vote):
    time_restriction = 3600
    db.execute("""DELETE FROM karma_voters WHERE ? - epoch >= 3600""",
            (time.time(),))
    db.commit()
    check = db.execute("""SELECT epoch FROM karma_voters WHERE voter=? AND votee=?""",
            (nick.lower(), nick_vote.lower())).fetchone()

    if check:
        check = check[0]
        if time.time() - check >= time_restriction:
            db.execute("""INSERT OR REPLACE INTO karma_voters(
                       voter,
                       votee,
                       epoch) values(?,?,?)""", (nick.lower(), nick_vote.lower(), time.time()))
            db.commit()
            return True, 0
        else:
            return False, timeformat.timeuntil(check, now=time.time() - time_restriction)
    else:
        db.execute("""INSERT OR REPLACE INTO karma_voters(
                   voter,
                   votee,
                   epoch) values(?,?,?)""", (nick.lower(), nick_vote.lower(), time.time()))
        db.commit()
        return True, 0


# TODO Make this work on multiple matches in a string, right now it'll only
# work on one match.
# karma_re = ('((\S+)(\+\+|\-\-))+', re.I)
karma_re = re.compile('(.+)(\+\+|\-\-)$', re.I)


@hook.regex(karma_re)
def karma_add(match, nick, db, notice):
    nick_vote = match.group(1).strip().replace("+", "")
    if nick.lower() == nick_vote.lower():
        notice("You can't vote on yourself!")
        return
    if len(nick_vote) < 3 or " " in nick_vote:
        return  # ignore anything below 3 chars in length or with spaces

    vote_allowed, when = allowed(db, nick, nick_vote)
    if vote_allowed:
        if match.group(2) == '++':
            db.execute("""INSERT or IGNORE INTO karma(
                       nick_vote,
                       up_karma,
                       down_karma,
                       total_karma) values(:nick,:up,?,?)""", (nick_vote.lower(), 0, 0, 0))
            up(db, nick_vote)
            notice("Gave {} 1 karma!".format(nick_vote))
        if match.group(2) == '--' and CAN_DOWNVOTE:
            db.execute("""INSERT or IGNORE INTO karma(
                       nick_vote,
                       up_karma,
                       down_karma,
                       total_karma) values(?,?,?,?)""", (nick_vote.lower(), 0, 0, 0))
            down(db, nick_vote)
            notice("Took away 1 karma from {}.".format(nick_vote))
        else:
            return
    else:
        notice("You are trying to vote too often. You can vote again in {}!".format(when))


@hook.command('karma', 'k')
def karma(inp, chan, db):
    """k/karma <nick> -- returns karma stats for <nick>"""

    if not chan.startswith('#'):
        return

    nick_vote = inp
    out = db.execute("""SELECT * FROM karma WHERE nick_vote=?""",
            (nick_vote.lower(),)).fetchall()

    if not out:
        return "That user has no karma."
    else:
        out = out[0]
        return "{} has {} karma points.".format(nick_vote, out[1] - out[2])
