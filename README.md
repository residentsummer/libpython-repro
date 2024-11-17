## Prepare image

    docker build -t libpython-repro .


## Reproduce crash

    docker run -it --rm libpython-repro bash -c 'cd /var/www; python3 -m core.app'


## Reproduce with local modifications

    docker run -v $PWD:/var/www -it --rm libpython-repro bash -c 'cd /var/www; python3 -m core.app'

