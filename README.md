# ModelDrivenDevelopment
Assigned Project for Model-Driven Development

## CLI Use of Repo Miner
python -m src.repo_miner fetch-commits --repo owner/repo [--max 100] --out commits.csv

Fetches up to max commits from owner/repo and puts the dataframe into the commits.csv file.