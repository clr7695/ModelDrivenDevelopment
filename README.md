# ModelDrivenDevelopment
Assigned Project for Model-Driven Development

## CLI Use of Repo Miner
python -m src.repo_miner fetch-commits --repo owner/repo [--max 100] --out commits.csv
Fetches up to max commits from owner/repo and puts the dataframe into the commits.csv file.

python -m src.repo_miner fetch-issues --repo owner/repo [--state all|open|closed] [--max 50] --out issues.csv
Fetches up to max issues from owner/repo in state and puts the dataframe into the issues.csv file.

python -m src.repo_miner summarize --commits commits.csv --issues issues.csv
Summarizes the issues and commits given.