# ⚠️ Archived

Lives on over here https://github.com/lurado/LLDO

# LLDB commands to make my life easier

Based on [Chisel](https://github.com/facebook/chisel)

## Commands

| Command | Description |
|---------|-------------|
| proofimage | Display an image saved on your local hard drive as fullscreen overlay |
| hsafearea  | Highlight the safe area insets of a given view |
| unhsafearea | Remove the safe area inset highlight on a view |
| hlayoutmargins | Highlight the layout margins of a given view |
| unhlayoutmargins | Remove the layout margin highlight on a view |


## Usage

Add 

```
script fblldb.loadCommandsInDirectory('/path/to/lldb_commands/')
```

to your `.lldbinit` file after the `command script import <chisel>` line.

## Development

1. `command source ~/.lldbinit`
1. run command
1. GOTO 1

## LICENSE

MIT - see LICENSE file
