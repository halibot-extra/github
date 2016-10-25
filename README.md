Halibot Github Module
=====================

Reports changes to github repositories.

How to use
----------

This module will spin up a server that will listen for github hook events. You
will need to enable a hook in your github repository or organization and have it
point to the server you are running this module on. The port number of the
server can be changed with the `port` instance config field (9000 by default). It is recommended
that you use a secret key shared between github and this module. This key can be
set with the `secret` field.

You will need to tell this module where to send the reports, which is done with
the `context` instance config field. You will also need to tell this module what
events and actions to listen for. This is done with the `events` field which is
a map of all events to listen for to a list of actions to listen for.

Example config
--------------

```json
{
  ...


  "module-instances": {
    ...

    "github-example": {
      "of": "github",
      "secret": "sshhhh",
      "dest": "irc0/##example",
      "events": {
        "issues": [
          "opened",
          "reopened",
          "closed"
        ],
        "pull_request": [
          "opened",
          "reopened",
          "closed"
        ]
      }
    }

    ...
  }
}
```
