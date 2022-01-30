## Generate CSV Export

This site describes the different steps necessary to generate and download a CSV export of transactions for different crypto exchanges and wallets.

### Binance

1. login to Binance
1. switch to `Wallet`=>`Fiat and Spot`
1. switch to `Transaction History`
1. click on `Generate all statements`
   1. choose the period (at most 3 months)
   1. choose `All` for account
   1. choose `All` for coin
   1. uncheck `Hide transfer record`
   1. click generate
1. repeat 4. until your limit (4 exports) is reached or you have started generation for all periods you need
   * when you need more than 4 reports you have to resume next month
1. wait for e-mail or SMS notification about finish of export generation
1. download exports
   * (recommendation) store at a safe long-lasting storage to be able to regenerate Accointing import without generation process
1. extract all files from downloaded archive
1. run accointing_convert on first file (based on date sort)
1. run accointing_convert on every following extracted file using option `--no-overwrite`
