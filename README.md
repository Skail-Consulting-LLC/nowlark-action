# Nowlark Notify and Ask

Send a push notification from a workflow to your iPhone, iPad, Mac or Apple Watch, or to your team's
on-call channel. Or ask a person a question and hold the job until they answer with one tap.

## Before you start

1. Install [Nowlark](https://nowlark.com) on your iPhone or Mac and, in the app, open Settings › **Connect an App** › **Create Your Key**. Copy the
   key when it is shown. It starts `nlk_`. A personal key reaches only your own devices; you can revoke it in the
   app at any time.
2. In your repository, open **Settings › Secrets and variables › Actions**, click **New repository secret**, name it
   `NOWLARK_API_KEY` and paste the key.

## Tell someone

```yaml
- uses: Skail-Consulting-LLC/nowlark-action@v1
  if: failure()
  with:
    api-key: ${{ secrets.NOWLARK_API_KEY }}
    title: ${{ github.workflow }} failed on ${{ github.ref_name }}
    priority: 1
```

Put this step after the steps it watches, in the same job. The notification opens this workflow run when tapped.

## Ask and wait for the answer

```yaml
jobs:
  approve:
    runs-on: ubuntu-latest
    steps:
      - uses: Skail-Consulting-LLC/nowlark-action@v1
        with:
          api-key: ${{ secrets.NOWLARK_API_KEY }}
          title: Deploy ${{ github.repository }} to production?
          body: ${{ github.sha }} by ${{ github.actor }}
          ask: approve_deny
          pass-on: approve
          wait: 1800
  deploy:
    needs: approve
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

Approve lets `deploy` run. Any other answer (Deny, or Later with `approve_deny_later`), or no answer within `wait`
seconds, fails the step. The question closes on the phone when the wait ends, so a late tap is refused and can
never approve a job that has already stopped. The runner is held while it waits, which counts toward your
Actions minutes.

## Inputs

| Input | Default | What it does |
|---|---|---|
| `api-key` | | Your `nlk_` key. Required. Pass it from a secret. |
| `title` | | The title, or the question when `ask` is set. Required. |
| `body` | | Text under the title. |
| `source` | the repository name | The sender name shown on the phone. |
| `url` | this workflow run | The link the notification opens. |
| `priority` | `0` | `-1` quiet, `0` normal, `1` high (time-sensitive, breaks through a Focus), `2` emergency (repeats until opened). |
| `ask` | | Make it a question: `approve_deny`, `yes_no`, `approve_deny_later`, `yes_no_later`, or up to 3 answers of your own, comma-separated (`Ship it,Hold`). |
| `wait` | `900` | Seconds to wait for the answer, within GitHub's 6-hour job limit. The question closes when the wait ends. |
| `pass-on` | | With `ask`: the answers that let the job go on, comma-separated, ignoring case. Any other answer fails the step. |
| `base-url` | `https://nowlark.com` | The Nowlark server. Leave it as it is. |

## Outputs

| Output | What it holds |
|---|---|
| `id` | The notification's id. |
| `answer` | The answer, when `ask` was set: `approve`, `deny`, `yes`, `no`, `later`, or one of your own answers. |

A channel key sends to your team's channel instead of to you, and the first member to answer answers for
the team, and the receipt names who answered. The action sends only the title, body, link and sender you set,
over HTTPS, and never prints your key. It runs on Linux and macOS runners, which include `python3`.

[API reference](https://nowlark.com/api) · [Support](https://nowlark.com/support)
