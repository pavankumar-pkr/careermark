with open("frontend/app.html", "r") as f:
    html = f.read()

# 1. Remove the broken early call
html = html.replace("if (token.value) { currentView.value = 'home'; loadAllData(); }", "")

# 2. Place it safely at the bottom after all functions are defined
html = html.replace("return { currentView,", "if (token.value) { currentView.value = 'home'; loadAllData(); }\n                return { currentView,")

with open("frontend/app.html", "w") as f:
    f.write(html)
