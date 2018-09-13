# Edit crontab
```
$ crontab -e
```

# List cron jobs
```
crontab -l

@hourly ~/projects/eqresponse-python/bin/download_feeds.sh month
@hourly ~/projects/eqresponse-python/bin/download_feeds.sh week

# 30 min
*/30 * * * * ~/projects/eqresponse-python/bin/download_feeds.sh day

# 5min
*/5 * * * * ~/projects/eqresponse-python/bin/download_feeds.sh hour
```
