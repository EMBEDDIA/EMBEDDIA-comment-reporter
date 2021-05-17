import argparse
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import bottle
import yaml
from bottle import Bottle, request, response, run
from bottle_swagger import SwaggerPlugin

from comment_reporter.comment_report_nlg_service import CommentReportNlgService

#
# START INIT
#

# CLI parameters
parser = argparse.ArgumentParser(description="Run the comment report generation server.")
parser.add_argument("port", type=int, default=8080, help="port number to attach to")
parser.add_argument("--force-cache-refresh", action="store_true", default=False, help="re-compute all local caches")
args = parser.parse_args()
sys.argv = sys.argv[0:1]

log = logging.getLogger("root")
log.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

rotating_file_handler = logging.handlers.RotatingFileHandler(
    Path(__file__).parent / "comment-reporter.log",
    mode="a",
    maxBytes=5 * 1024 * 1024,
    backupCount=2,
    encoding=None,
    delay=0,
)
rotating_file_handler.setFormatter(formatter)
rotating_file_handler.setLevel(logging.INFO)

log.addHandler(stream_handler)
log.addHandler(rotating_file_handler)

# Bottle
app = Bottle()
service = CommentReportNlgService(random_seed=4551546)

# Swagger
with open(Path(__file__).parent / "swagger.yml", "r") as file_handle:
    swagger_def = yaml.load(file_handle, Loader=yaml.FullLoader)
app.install(
    SwaggerPlugin(swagger_def, serve_swagger_ui=True, swagger_ui_suburl="/documentation/", validate_requests=False)
)

log.info("here")


def allow_cors(opts):
    def decorator(func):
        """ this is a decorator which enables CORS for specified endpoint """

        def wrapper(*args, **kwargs):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(opts)
            response.headers["Access-Control-Allow-Headers"] = (
                "Origin, Accept, Content-Type, X-Requested-With, " "X-CSRF-Token"
            )

            # Only respond with body for non-OPTIONS
            if bottle.request.method != "OPTIONS":
                return func(*args, **kwargs)

        return wrapper

    return decorator


LANGUAGES = ["en", "fi"]

#
# END INIT
#


def generate(language: str, comments: List[str]) -> Tuple[str, List[str]]:
    return service.run_pipeline(language, comments)


@app.route("/report", method=["POST", "OPTIONS"])
@allow_cors(["POST", "OPTIONS"])
def api_generate_json() -> Dict[str, Any]:

    parameters = request.json

    if not parameters:
        response.status = 400
        return {"errors": ["Missing or empty request body"]}

    comments = parameters.get("comments")
    language = parameters.get("language")

    errors = []

    if language not in LANGUAGES:
        errors.append("Invalid or missing language. Query /languages for valid options.")
    if not comments:
        errors.append("Invalid or missing comment list.")
    if errors:
        response.status = 400
        return {"errors": errors}

    body, errors = generate(language, comments)
    output = {"language": language, "body": body}
    if errors:
        output["errors"] = errors
    return output


@app.route("/languages", method=["GET", "OPTIONS"])
@allow_cors(["GET", "OPTIONS"])
def get_languages() -> Dict[str, List[str]]:
    return {"languages": LANGUAGES}


@app.route("/health", method=["GET", "OPTIONS"])
@allow_cors(["GET", "OPTIONS"])
def health() -> Dict[str, Any]:
    return {"version": "1.0.0"}


def main() -> None:
    log.info("Starting server at 8081")
    run(app, server="meinheld", host="0.0.0.0", port=8081)
    log.info("Stopping")


if __name__ == "__main__":
    main()
