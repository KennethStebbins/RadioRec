# RadioRec
Record radio streams!

# Usage Example

```sh
docker run --rm -v /folder/on/host:/output -e "TZ=America/Los_Angeles" kennethstebbins/radiorec:latest --url <listenlive.co URL>
```

- `-v /folder/on/host:/output`
    - This is where all the recordings will be placed
- `-e "TZ=America/Los_Angeles`
    - Sets the timezone so that --start-date and --end-date use your local time and date
- `--url <listenlive.co URL>`
    - Specify a radio station's listenlive.co page URL for RadioRec to scrape