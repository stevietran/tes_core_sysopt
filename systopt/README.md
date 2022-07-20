# Build and run docker

`docker build -t tes_sys .`

`docker run --name tes_sys -p 8000:8000 tes_sys`

# Setting conda env variable

`conda env config vars set PYTHONPATH='/home/vutran/code/docker/tes-app/tes_core_sysopt/systopt:$PYTHONPATH'`

`conda activate tes_sys_opt`