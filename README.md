# gimme-those-pics-bot

<div align="center">
  <img src="imgflip.jpg" alt="Image Description" width="600">
  <h3>
    Need your memes, GIFs, and cat pics all in one tidy archive?
    Let this Discord bot take care of the hard work for you! 😼🌈
  </h3>
  <h3>
    <a href="https://discord.com/oauth2/authorize?client_id=1325165713727684658&permissions=101376&integration_type=0&scope=applications.commands+bot">
    Click here to invite your new favorite bot! 🚀</a>
  </h3>
</div>

## Usage

``` !gimme [channel=general] [start_date=YYYY-MM-DD] [end_date=YYYY-MM-DD] [extensions=ext1,ext2,...] ```

The `!gimme` command allows you to download attachments from a Discord channel based on a specified date range and/or file extensions. The bot creates one or more ZIP files containing the matching attachments and sends them in the channel.

- **Parameters**:
  - `channel` (optional): The channel you want to get attachments from.
  - `start_date` (optional): Filters attachments starting from this date. Accepted formats: `YYYY-MM-DD`, `DD-MM-YYYY`, `YYYY/MM/DD`, or `DD/MM/YYYY`.
  - `end_date` (optional): Filters attachments up to this date. Accepted formats: Same as `start_date`.
  - `extensions` (optional): Comma-separated list of file extensions to include (e.g., `jpg,png,pdf`).

- **Defaults**:
  - If `channel` is not provided, the command will default to the channel from which it was executed.
  - If `start_date` is not provided, it defaults to one day before the current date.
  - If `end_date` is not provided, it defaults to the current date.
  - If no `extensions` are specified, the bot retrieves all attachments regardless of type.

## Examples

1. **Download all attachments within a date range**:

    ``` !gimme start_date=2025-01-01 end_date=2025-01-05 ```

2. **Download images (e.g., jpg, png) from the past day**:

    ``` !gimme extensions=jpg,png ```

3. **Download files for a specific day and type**:

    ```!gimme start_date=2025-01-01 extensions=pdf```

4. **Download all attachments up to a specific date**:

    ``` !gimme end_date=2025-01-10 ```

5. **Download all attachments from the past day**:

    ``` !gimme ```

6. **Download attachments from a specific channel (given a channel name)**:

    ``` !gimme general start_date=2025-01-01 extensions=pdf ```

7. **Download attachments from a specific channel (given a channel ID)**:

    ``` !gimme 123456789012345678 start_date=2025-01-01 extensions=pdf ```
