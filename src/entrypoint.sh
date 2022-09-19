#! /bin/bash
set -e

if [ -z "$1" ] # nothing specified so we bootstrap the service itself
then

    stop() {
        echo "Received SIGINT or SIGTERM. Shutting down $DAEMON"
        # Get PID
        pid=$(cat /var/run/sshd/sshd.pid)
        # Set TERM
        kill -SIGTERM "${pid}"
        # Wait for exit
        wait "${pid}"
    }

    echo "Starting sshd"
    trap stop SIGINT SIGTERM

    mkdir -p /var/run/sshd
    # Log to the stdout of process with id 1 (this script since it is the entrypoint in the docker)
    # This way the sshd logs show up in the container logs
    /usr/sbin/sshd -e -D -o ListenAddress=0.0.0.0 &
    pid="$!"
    echo "${pid}" > /var/run/sshd/sshd.pid
    wait "${pid}" && exit $?

elif [ "$1" = "bash" ]  # run a regular bash shell
then
    exec bash "${@:2}"
else # pass any other params directly to nubbs to handle
    exec nubbs "$@"
fi

