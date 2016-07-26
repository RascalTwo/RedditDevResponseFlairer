# Reddit Dev Response Flairer

Append ` | Dev Response` to post flair text that have been responded to by devs.

*****

# Dependancies

*****

- PRAW

Makes posts using the PRAW library while tracking posts made and history via a sqlite3 database.

*****

# Configuration

*****

All configurations are made via the `config.json` file.

```JSON
{
    "user_agent": "",
    "username": "",
    "password": "",
    "check_rate": 60,
    "subreddits": [
        "JoinSquad"
    ],
    "developer_flairs": [
        "DeveloperFlair"
    ],
    "developers": [

    ]
}
```

- `user_agent`
    - What Google and Reddit sees the bot as, the more unique this is the better.
- `username`
    - Username of the reddit account making the posts.
- `password`
    - Password of the Reddit account making the posts.
- `check_rate`
    - How often to check for new comments.
- `subreddits`
    - List of subreddits to run in.
- `developer_flairs`
    - Flairs that belong to developers.
- `developers`
    - List of developer usernames.

> `developers` and `developer_flairs` are both case sensitive.

*****

# Technical Breakdown

*****

## Databases

*****

The bot has three database tables, `posts` and `processed`.

### Posts

ID  | UTC | Comment
--- | --- | ---
1234567 | 1469504597 | https://www.reddit.com/r/joinsquad/comments/4uk572/night_maps_are_useless_if_you_can_turn_up_the/d5qcedn

Contains all posts that have a dev has responded to.

Also contains a permalink to the comment that changed the flair text of the post.

Only 1000 entries are kept in the table.

### Processed

ID  |  UTC
--- |  ---
1234567 | 1469504597

Contains all comments that have been processed.

Only 1000 entries are kept in the table.

*****

## Walkthough

*****

- Tables and triggers are created if they're don't already exist.
- Reddit is logged into.
- While the bot is running:
    - For every comment made in /r/JoinSquad:
        - If ID of comment in `processed`, skip. Otherwise continue below.
        - Add comment ID to `processed` list.
        - If any of these three statements are true, skip the comment:
            - Flair CSS of the comment author is not `DeveloperFlair`.
            - Post ID in `posts`.
            - ` | Dev Response` in flair text.
        - Add Post ID to `posts`.
        - Add ` | Dev Response` to the flair text.
