#!/usr/bin/env python3
"""
Convert different crypto exchange exports to Accointing CSV
"""

import os
import sys
import mimetypes
import subprocess
import csv
import hashlib
import datetime
import shutil
import tempfile
from logging import getLogger, DEBUG, ERROR, INFO
from pathlib import Path


LOGGER_NAME = "ACSV_log"
SOFFICE_ARGS = {
    "libreoffice": ["--convert-to", "csv"],
    "fallback": ["--convert-to", "csv"],
}
MODULE_MAP = {
    "yaml": "PyYAML",
    "coloredlogs": "coloredlogs colorama",
}
HASH_FIELDS = [
    "date",
    "transactionType",
    "inBuyAmount",
    "inBuyAsset",
    "outSellAmount",
    "outSellAsset",
]
SCRIPT_DIR = Path(os.path.realpath(__file__)).parent


def __version():
    """return version from version.txt or default"""
    version_file = Path(os.path.realpath(__file__)).parent.joinpath("version.txt")
    if not version_file.exists():
        return "0.1a1"
    with version_file.open("r", encoding="UTF-8") as f_h:
        return f_h.readlines()[0]


__version__ = __version()


def dep_error(module: str):
    """print dependency error message"""
    require_txt = SCRIPT_DIR.joinpath("requirements.txt")
    package = MODULE_MAP.get(module, module)
    print(
        f"Required module {module} not found.\n\n"
        "Please install it, e.g.:\n"
        f"* pip3 install {package}\n"
        f"* pip3 install -r {require_txt}"
    )
    sys.exit(5)


try:
    import requests
    import configargparse
    import yaml
    import coloredlogs
except ModuleNotFoundError as mod_err:
    dep_error(mod_err.name)


class _DescriptionAction(configargparse.Action):
    """
    custom action to list all available description definitions
    """

    # pylint: disable=redefined-builtin
    def __init__(
        self,
        option_strings,
        dest=configargparse.SUPPRESS,
        default=configargparse.SUPPRESS,
        help="show available descriptions",
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        desc_path = SCRIPT_DIR.joinpath("descriptions")
        msg = ["The following descriptions are known:\n\n"]
        msg.extend(
            [
                desc.name.replace(".yaml", "\n")
                for desc in desc_path.iterdir()
                if desc.is_file()
                and not desc.name.startswith("sample")
                and desc.suffix == ".yaml"
            ]
        )
        parser.exit(message="* ".join(msg))


class AccointingCsv:
    """
    class to manage CSV template of Accointing
    """

    def __init__(self, **kwargs):
        self.cache_dir = Path(kwargs.get("cache_dir", tempfile.mkdtemp(prefix="acsv_")))
        self.logger = getLogger(LOGGER_NAME)
        self.template_dict = {"order": [], "map": {}}
        self.soffice = self._get_soffice(kwargs.get("soffice_path"))
        self.logs = {"warning": [], "info": [], "error": []}
        # define fields to be used to generate reproducable transaction ID
        # using hashing of their values
        desc_path = Path(kwargs.get("description"))
        descriptions = SCRIPT_DIR.joinpath("descriptions")
        if not desc_path.exists():
            desc_path = descriptions.joinpath(kwargs.get("description"))
        if not desc_path.exists():
            desc_path = descriptions.joinpath(f"{kwargs.get('description')}.yaml")
        if not desc_path.exists():
            raise RuntimeError(
                f"Could not find given description '{kwargs.get('description')}' in "
                f"'{descriptions}'",
            )
        with desc_path.open("r", encoding="UTF-8") as f_h:
            self.description = yaml.safe_load(f_h)
            self.description.update({"name": kwargs.get("description")})

    @property
    def error(self):
        """return stored error"""
        return self.logs.get("error")

    @error.setter
    def error(self, msg: str):
        """store given warning for post-poned output"""
        if msg not in self.logs.get("error"):
            self.logs["error"].append(msg)

    @property
    def fieldnames(self):
        """return fieldnames of CSV template"""
        fieldnames = []
        for short_field in self.template_dict.get("order"):
            fieldnames.append(self.get_field(short_field))
        return fieldnames

    @property
    def info(self):
        """return stored info"""
        return self.logs.get("info")

    @info.setter
    def info(self, msg: str):
        """store given warning for post-poned output"""
        if msg not in self.logs.get("info"):
            self.logs["info"].append(msg)

    @property
    def warning(self):
        """return stored warnings"""
        return self.logs.get("warning")

    @warning.setter
    def warning(self, msg: str):
        """store given warning for post-poned output"""
        if msg not in self.logs.get("warning"):
            self.logs["warning"].append(msg)

    def _get_soffice(self, soffice: str = ""):
        """return path to soffice"""
        if soffice:
            soffice_path = Path(self.soffice)
            if not soffice_path.exists() and not (
                soffice_path.is_file() or soffice_path.is_symlink()
            ):
                raise ProcessLookupError(
                    "Given soffice-path is not valid. Please check '--soffice-path'."
                )
            return soffice
        soffice = shutil.which("soffice")
        if not soffice:
            raise ProcessLookupError(
                "Required command soffice not found. "
                "Please install LibreOffice or use '--soffice-path'."
            )
        return soffice

    def prepare_template(self, template_url: str):
        """download and prepare Accointing template"""
        filename = Path(template_url).name
        template_filepath = template_url
        if template_url.startswith("http"):
            headers = {"user-agent": f"acsv-agent/{__version__}"}
            with requests.get(template_url, stream=True, headers=headers) as resp:
                resp.raise_for_status()
                filename = resp.url.rsplit("/", 1)[1].split("?", 1)[0]
                template_filepath = self.cache_dir.joinpath(filename)
                with open(template_filepath, "wb") as f_h:
                    for chunk in resp.iter_content(chunk_size=128):
                        f_h.write(chunk)
        if not filename.endswith(".csv") and mimetypes.guess_type(
            template_filepath
        ) not in ["text/csv", "text/tab-separated-values"]:
            template_filepath = self.convert_template(template_filepath)
        with open(template_filepath, "r", encoding="UTF-8") as f_h:
            dialect = csv.Sniffer().sniff(f_h.read(1024))
            f_h.seek(0)
            for field in list(csv.reader(f_h, dialect=dialect))[0]:
                short_field = field.split(" ", 1)[0]
                self.template_dict["map"].update({short_field: field})
                self.template_dict["order"].append(short_field)

    def convert_template(self, template_filepath: Path):
        """convert template to csv"""
        self.logger.info(
            "Given file %s is not of type CSV or TSV. Preparing for conversion.",
            template_filepath,
        )
        self.logger.info("Starting conversion using %s.", self.soffice)
        try:
            run_soffice_name = subprocess.run(
                [self.soffice, "--version"],
                capture_output=True,
                check=True,
                shell=False,
            )
        except subprocess.CalledProcessError as err:
            raise ProcessLookupError(
                f"Couldn't detect soffice name:\n\n{err.stderr}"
            ) from err
        soffice_name = (
            run_soffice_name.stdout.decode("UTF-8").strip().split(" ", 1)[0].lower()
        )
        cmd = (
            [self.soffice]
            + SOFFICE_ARGS.get(soffice_name, SOFFICE_ARGS.get("fallback"))
            + [template_filepath]
        )
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as err:
            raise RuntimeError(
                "Error while converting to CSV using "
                f"'{' '.join(cmd)}':\n\n"
                f"STDOUT: {err.stdout}\n\n"
                f"STDERR: {err.stderr}"
            ) from err
        return Path(f"{template_filepath.name.rsplit('.', 1)[0]}.csv")

    def create_csv(
        self, source_file: str, target_file: str, no_overwrite: bool = False
    ):
        """create CSV based on given data"""
        with open(source_file, "r", encoding="UTF-8") as fh_read:
            dialect = csv.Sniffer().sniff(fh_read.read(2048))
            fh_read.seek(0)
            write_mode = "w"
            write_header = True
            if no_overwrite:
                write_mode = "a"
                # when target exists and has content we assume it already has a header
                if (
                    Path(target_file).exists()
                    and Path(target_file).stat().st_size > 1024
                ):
                    write_header = False
            with open(
                target_file, write_mode, newline="", encoding="UTF-8"
            ) as fh_write:
                write_csv = csv.DictWriter(fh_write, fieldnames=self.fieldnames)
                if write_header:
                    write_csv.writeheader()
                for row in csv.DictReader(fh_read, dialect=dialect):
                    if self.skip_row(row):
                        continue
                    write_csv.writerow(self.convert_row(row))

    def convert_row(self, row: dict):
        """convert CSV row to CSV template format"""
        row_dict = {}
        for short_field in self.template_dict.get("order"):
            row_dict.update(
                {self.get_field(short_field): self.get_field_value(row, short_field)}
            )
        if self.description.get("description").get("operationId").get("generate"):
            trans_id = self.generate_trans_id(row)
            row_dict.update({self.get_field("operationId"): trans_id})
        row_dict.update({"date": self.get_row_date(row)})
        return row_dict

    def skip_row(self, row: dict):
        """check if row matches skip definition"""
        if not self.description.get("description").get("skip_rows"):
            return False
        for skip in self.description.get("description").get("skip_rows"):
            if row.get(skip.get("field")) == skip.get("value"):
                return True
        return False

    def get_row_date(self, row: dict):
        """return formated date of row"""
        timestamp = datetime.datetime.strptime(
            row.get(self.description.get("description").get("date").get("field")),
            self.description.get("description").get("date").get("format"),
        )
        return timestamp.strftime("%m/%d/%Y %H:%M:%S")

    def get_field(self, short_field: str):
        """return long name of given short field"""
        return self.template_dict.get("map").get(short_field)

    def get_field_value(self, row: dict, short_field: str, follow_map: bool = True):
        """return value for given short field"""
        src_field = self.description.get("description").get(short_field)
        if src_field is None:
            self.error = (
                f"Accointing field '{self.get_field(short_field)}' is missing in "
                f"description '{self.description.get('name')}', skipping"
            )
            return ""
        if src_field is False:
            self.info = (
                f"Accointing field '{self.get_field(short_field)}' is not mapped for "
                f"description '{self.description.get('name')}', skipping"
            )
            return ""
        if not isinstance(src_field, dict):
            return row.get(src_field)
        return self.get_field_value_from_map(
            row=row, src_field=src_field, follow_map=follow_map
        )

    def get_field_value_from_map(
        self, row: dict, src_field: dict, follow_map: bool = True
    ):
        """return value after analyzing map"""
        map_name = src_field.get("map")
        if not map_name:
            return ""
        field_map = self.description.get(map_name)
        if not field_map:
            raise RuntimeError(
                f"Mapping '{map_name}' not found in description "
                f"'{self.description.get('name')}'"
            )
        check_field = row.get(field_map.get("field"))
        if check_field not in field_map.get("map", {}) and not field_map.get("default"):
            raise RuntimeError(
                f"Value '{check_field}' for field '{field_map.get('field')}' not found in "
                f"mapping '{map_name}' of description '{self.description.get('name')}'"
            )
        if field_map.get("map", {}).get(check_field) is False:
            return ""
        if field_map.get("map", {}).get(check_field, {}).get("field"):
            return row.get(field_map.get("map").get(check_field).get("field"))
        if field_map.get("default", {}).get("field"):
            return row.get(field_map.get("default").get("field"))
        if not follow_map:
            return check_field
        return field_map.get("map").get(check_field).get("value")

    def generate_trans_id(self, row: dict, fields: list = None):
        """generate ID for given transaction"""
        hash_fields = fields or HASH_FIELDS
        checksum = hashlib.sha256(self.get_row_date(row).encode("UTF-8"))
        for short_field in hash_fields:
            checksum.update(
                self.get_field_value(row, short_field, follow_map=False).encode("UTF-8")
            )
        return checksum.hexdigest()


def get_arguments():
    """process provided arguments"""
    config_filename = "accointing_convert.yaml"
    config_files = list(
        filter(
            None,
            [
                str(Path(os.getenv("XDG_CONFIG_HOME")).joinpath(config_filename))
                if os.getenv("XDG_CONFIG_HOME")
                else None,
                str(Path().home().joinpath(".config", config_filename)),
            ],
        )
    )
    parser = configargparse.ArgParser(
        "Accointing Convert",
        description="Tool to convert crypto exchange CSV to Accointing CSV",
        default_config_files=config_files,
        args_for_setting_config_path=["-c", "--config"],
        args_for_writing_out_config_file=["--write-config"],
        auto_env_var_prefix="ACSV_",
        add_env_var_help=True,
        add_config_file_help=True,
        config_file_parser_class=configargparse.YAMLConfigFileParser,
    )
    parser.add_argument("source_file", help="file path of CSV that should be converted")
    parser.add_argument("target_file", help="file path to store generate CSV into")
    parser.add_argument(
        "-d",
        "--description",
        required=True,
        help="CSV description to be used for conversion.",
    )
    parser.add_argument(
        "-l",
        "--list-descriptions",
        action=_DescriptionAction,
    )
    parser.add_argument(
        "--cache-dir",
        default=tempfile.mkdtemp(prefix="acsv_"),
        help=(
            "directory to cache template files "
            f"(Default: unique directory in {tempfile.gettempdir()})"
        ),
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="do not overwrite existing target file (default is overwrite)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="show only error output"
    )
    parser.add_argument(
        "--soffice-path", help="provide path to LibreOffice binary for CSV conversion"
    )
    parser.add_argument(
        "-t",
        "--template-url",
        default="https://www.accointing.com/app/templates/Accointing_template.xlsx",
        help="path or web URL to Accointing template",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show verbose output"
    )
    parser.add_argument(
        "-V", "--version", action="version", help="show version", version=__version__
    )
    return parser.parse_args()


def main():
    """main function"""
    args = get_arguments()
    log_level = INFO
    if args.quiet:
        log_level = ERROR
    if args.verbose:
        log_level = DEBUG
    logger = getLogger(LOGGER_NAME)
    coloredlogs.install(level=log_level, logger=logger)
    logger.setLevel(log_level)
    try:
        template = AccointingCsv(**args.__dict__)
    except RuntimeError as error:
        logger.error("could not load description: %s", error)
        sys.exit(4)
    # pylint: disable=broad-except
    try:
        template.prepare_template(template_url=args.template_url)
    except FileNotFoundError as error:
        logger.error("Template file '%s' not found", error.filename)
        sys.exit(5)
    except RuntimeError as error:
        logger.error("template conversion failed: %s", error)
    except Exception as error:
        logger.error("could not prepare CSV template: %s", error)
        sys.exit(5)
    try:
        template.create_csv(args.source_file, args.target_file, args.no_overwrite)
    except FileNotFoundError as error:
        logger.error("file '%s' not found", error.filename)
        sys.exit(6)
    except RuntimeError as error:
        logger.error("configuration error processing CSV: %s", error)
        sys.exit(6)
    for log in template.info:
        logger.info(log)
    for log in template.warning:
        logger.warning(log)
    for log in template.error:
        logger.error(log)


if __name__ == "__main__":
    main()
