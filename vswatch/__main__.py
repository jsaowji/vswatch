
from .http_backend import launch_http_backend
from .vs_stuff import load_script

if __name__ == "__main__":
    import sys
    import threading
    import functools
    import subprocess

    selection = "01"

    if len(sys.argv) > 2:
        selection = sys.argv[2]

    if len(sys.argv) <= 1:
        print("no script provided")
        sys.exit(1)

    files = load_script(sys.argv[1],selection)
    filenames = [ a.name for a in files ]


    #gigantic hack
    from socket import socket
    port = 8989
    with socket() as s:
        s.bind(('',0))
        port = s.getsockname()[1]

    mpv_base = f"http://127.0.0.1:{port}/"


    def websoer(hostName,serverPort,files):
        global webServer
        print("Server started http://%s:%s" % (hostName, serverPort))

        webServer = launch_http_backend(hostName,serverPort,files)
        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass
        webServer.server_close()
        print("Server stopped.")

    httpthread = threading.Thread(target=functools.partial(websoer,hostName="127.0.0.1",serverPort=port,files=files))
    httpthread.start()

    
    cmds = [ "mpv" ]
    
    for f in filenames:
        if f.endswith("y4m"):
            cmds += [ f"{mpv_base}{f}" ]
        elif f.endswith("wav"):
            cmds += [ f"--audio-file={mpv_base}{f}" ]
        elif f.endswith("ffmetadata"):
            cmds += [ f"--chapters-file={mpv_base}{f}" ]
    subprocess.Popen(cmds).wait()
    webServer.shutdown()
