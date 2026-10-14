with open("api/v1/platform.py", "r") as f:
    content = f.read()

# Replace the crashing line with a safe fallback
old_line = 'o.closing_date.strftime("%Y-%m-%d")'
new_line = 'o.closing_date.strftime("%Y-%m-%d") if o.closing_date else "No Deadline"'
content = content.replace(old_line, new_line)

with open("api/v1/platform.py", "w") as f:
    f.write(content)
