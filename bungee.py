from cloudbot import hook
 
import requests
 
@hook.command("bungee", "bungeecord", autohelp=False)
def bungee():
    """-- Gets the latest Bungee build number and download link."""
    
    try:
        request = requests.get("http://ci.md-5.net/job/BungeeCord/lastStableBuild/buildNumber")
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
        return "I couldn't find the latest build number for BungeeCord, but you can download it here: http://ci.md-5." \
               "net/job/BungeeCord/lastStableBuild/artifact/bootstrap/target/BungeeCord.jar"
 
    latest = request.text
    return "The latest BungeeCord build is \x02#" + latest + "\x02, and can be downloaded from http://ci.md-5." \
           "net/job/BungeeCord/" + latest + "/artifact/bootstrap/target/BungeeCord.jar"
