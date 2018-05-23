
Kolibri Demo Server Automation
==============================

Use cases:
  - in-Kolibri preview for content developers
  - partnerships support
  - Channel Q/A process 

Out of scope:
  - perf-team (see velox, and Punta Loma projects)
  - official demo servers
  - LE devs personal Kolibri dev servers?



CLI
---
To create a demo server for Channel X running at channelx.demo.learningequality.org,
SushOps engineers can follow the following two-step procedure:


1. Add a row to the demo server inventory
   - nickname: channelx
   - facility name and tyope
   - channel_ids to import
   - Kolibri pex URL

2. Setup the demoserver

         fab -R channelx-demo  demoserver



Behind the scenes, the role selector `-R channelx-demo` will point all commands
to the right container

TODO: update the existing logic to use container instead of VM:

    @task
    def demoserver():
        install_base()            # NOT NEEDED since container will have it
        download_kolibri()
        configure_nginx()         # NOT NEEDED; just serve on port 8080
        configure_kolibri()       # move logic to entrypoint.sh
        setup_kolibri()           # move logic to entrypoint.sh
        import_channels()         # move logic to entrypoint.sh



Demo Service API
----------------
We can expose the "create a demo server" functionality as an API that can be used
by Sushibar. This will allow non-technical people to spin-up demo servers as needed
for partner meetings and Q/A.


Credentials
-----------
  - creating a demo server requires the docker-machine certs and ssh key needed to connet to the demohost
    (no need for GCP creds)
  - share credentials using https://www.npmjs.com/package/machine-share
  - Shared device owner credentials for each demo server


Tech stack
----------
  - docker-host for base docker environment
  - Docker
  - git (pull latest pex from release tag or pex URL)
  - Fabric3
  - traefik for ingress
  - bonus portainer for monitoring



Design
------
  - Run Kolibri in a container
    - create facility on first run if none
    - specify hostname using labels in the docker compose file:
          labels:
           - 'traefik.enable=true'
           - 'traefik.backend=channel'
           - 'traefik.port=8000'
           - 'traefik.frontend.rule=Host:channel.demo.learningequality.org'

    - traefik for ingress will route to the right container based on sub-subdomain.
    - need to set DNS `*.demo.learningequality.org` to demohost


