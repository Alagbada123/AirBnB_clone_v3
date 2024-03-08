#!/usr/bin/python3
"""
Fabric script that generates a .tgz archive from the contents of the web_static
folder and distributes it to web servers.
"""
import os
from datetime import datetime

from fabric.api import env, local, put, run, task

# List of servers to deploy to
env.hosts = ["34.234.193.86", "54.90.40.86"]


def do_pack():
    """
    Generates a .tgz archive from the contents of the web_static folder.
    The archive is stored in the 'versions' folder.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive_name = "web_static_{}.tgz".format(timestamp)
    archive_path = os.path.join("versions", archive_name)

    # Create 'versions' directory if it doesn't exist
    if not os.path.exists("versions"):
        os.mkdir("versions")

    # Create a .tgz archive of the web_static directory
    print("Packing web_static to {}".format(archive_path))
    result = local(
            "tar -cvzf {} web_static".format(archive_path),
            capture=False
            )

    if result.return_code == 0:
        size = os.path.getsize(archive_path)
        print("web_static packed: {} -> {}Bytes".format(archive_path, size))
        return archive_path
    else:
        return None


def do_deploy(archive_path):
    """
    Distributes an archive to your web servers
    """
    if not os.path.exists(archive_path):
        return False

    try:
        # Upload the archive to the /tmp/ directory of the web server
        put(archive_path, "/tmp/")
        # Uncompress the archive to the folder /data/web_static/releases/
        archive_name = os.path.basename(archive_path)
        archive_name_no_ext = archive_name.split(".")[0]
        run("mkdir -p /data/web_static/releases/{}/".format(
            archive_name_no_ext
            ))
        run(
            "tar -xzf /tmp/{} -C /data/web_static/releases/{}/".format(
                archive_name, archive_name_no_ext
            )
        )
        # Delete the archive from the web server
        run("rm -rf /tmp/{}".format(archive_name))
        # Delete the symbolic link /data/web_static/current from the web server
        run("rm -rf /data/web_static/current")
        # Create a new the symbolic link /data/web_static/current on server
        # linked to the new version of your code
        run(
            "ln -s /data/web_static/releases/{}/ "
            "/data/web_static/current".format(
                archive_name_no_ext
            )
        )
        print("New version deployed!")
        return True
    except Exception:
        return False


@task(default=True)
def deploy():
    """
    Creates and distributes an archive to the web servers.
    """
    archive_path = do_pack()
    if archive_path is None:
        return False
    return do_deploy(archive_path)