## Accointing Convert

Accointing Convert is designed to convert crypto currency transaction exports in CSV format for importing into [Accointing](https://accointing.com).

The conversion is definded by description files that map columns of the export to columns known by Accointing importer.

The generated file can be imported using the [manual import](https://hub.accointing.com/our-crypto-platform/connecting-your-exchange/import-accointing-com-data-faqs) method.

[![Andrwe - accointing-convert](https://img.shields.io/static/v1?label=Andrwe&message=accointing-convert&color=blue&logo=github)](https://github.com/Andrwe/accointing-convert "Go to GitHub repo")
[![stars - accointing-convert](https://img.shields.io/github/stars/Andrwe/accointing-convert?style=social)](https://github.com/Andrwe/accointing-convert)
[![forks - accointing-convert](https://img.shields.io/github/forks/Andrwe/accointing-convert?style=social)](https://github.com/Andrwe/accointing-convert)

[![issues - accointing-convert](https://img.shields.io/github/issues/Andrwe/accointing-convert)](https://github.com/Andrwe/accointing-convert/issues)
[![Project - Roadmap/Tasks](https://img.shields.io/badge/Project-Roadmap%2FTasks-2ea44f?logo=github)](https://github.com/users/Andrwe/projects/1/views/1)
[![GitHub release](https://img.shields.io/github/release/Andrwe/accointing-convert?include_prereleases=&sort=semver&color=blue)](https://github.com/Andrwe/accointing-convert/releases/)

[![License](https://img.shields.io/badge/License-UNLICENSE-blue)](#license)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Andrwe/accointing-convert/main.svg)](https://results.pre-commit.ci/latest/github/Andrwe/accointing-convert/main)

### Usage

#### Convert Exports

1. [generate CSV based transaction exports](./generate_csv/)
1. run accointing_convert using the exports

#### Create Description

Description files in YAML format are used to define the conversion process.
This is done by connecting columns in export CSV to the columns required in the import CSV.
Due to the different export formats used by different exchanges and wallets the description file supports mapping of values and columns based on an other column.

To create a description file follow these steps:

1. fork [the main repository](https://github.com/Andrwe/accointing-convert/)
1. copy `descriptions/sample.yaml` to a file within `descriptions/` called like the exchange/wallet you are describing
1. edit the copied file to match columns of export CSV to columns used by Accointing

### Caveats

Due to limitation of the import system of Accointing not classifications available via web-app can be defined in the import file. (see [this forum post](https://community.accointing.com/t/classification-value-confusion-doc-vs-template-vs-import/8559) for details)

To help determining affected transactions accointing_convert lists all transaction with non-importable classification as warning after converting.


### License

Released under [UNLICENSE](/LICENSE) by [@Andrwe](https://github.com/Andrwe).
