# Twack Readme

Track your Twitter followers over time.

## Status

This works, but is pretty bare-bones at present. It's a personal project, but
the code is pretty high quality, and should even be getting some tests pretty
soon.

## Installation

Create a config file first, and store it in one of ``,``, or ``. It should look
something like this:

```ini
[twitter]
consumer_key: <twitter-consumer-key>
consumer_secret: <twitter-consumer-secret>

[database]
url: postgresql://<user>:<password>@<db-host>/<db-name>
```

Run `twack initdb` to create your database. If the configuration is correct, it
should exit without printing anything.

Set up a cron job that runs `twack load` at whatever frequency you want. This
should probably be a minimum of an hourly job, and more sensibly something like
daily or weekly.

There's no output at the moment. Reporting commands are coming at some point.
At the moment you'll need to just run queries directly against your postgres
db.

## To Do

1. Improve installation and documentation.
1. Tests. Lots of tests.
1. Reporting tools.
1. Web service built on the database?
