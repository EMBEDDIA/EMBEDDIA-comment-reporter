# Report generator from comments

## Running and setup

The comment reporter is dockerized, and should primarily be run as a standard docker container. The server runs in port 8081, which can be mapped via the standard docker commands to something else. Swagger-documentation of the API is available.

It is dependent on the following four microservices (all dockerized as well), which need to be accessible via HTTP(s):
- https://github.com/EMBEDDIA/comment-filter
- https://github.com/EMBEDDIA/EMBEDDIA-sentiment-analysis-service
- https://github.com/EMBEDDIA/EMBEDDIA-summarization-service
- https://github.com/EMBEDDIA/croatian_topic_api

The file `config.ini` needs to be modified to point the comment report generator at these services.

## Dependencies

### FOMA

The morphological realization for English is dependent on the Foma library. On ubuntu/debian, this should be available
from `apt`.

### Python dependencies

The software is being developed using python 3.6, which is the only officially supported version. At the same time,
we see no reason why the Reporter would fail to run on never versions of Python as well. Let us now if you come
across any problems.

Python library dependencies are defined in requirements.txt, and can be installed by running

```bash
 $ pip install -r requirements.txt
```

Again, we've only really tested the software using the specific versions listed in the file.

## Formatting, linting, etc.

The project is set up for use of `isort`, `black` and `flake8`. 

It's notable that `isort` is only used to *order* the imports (something `black` can't do), but `black`'s *formatting* 
is to be preferred over `isort`. What this means is that **`black` must be ran after `isort`**.

Manually run the formatters and linting with
```
 $ isort -rc . && black . && flake8 .
```

You can run
```
 $ pre-commit install
```
to force git to run both `black` and `flake8` for you before it allows you to commit.
