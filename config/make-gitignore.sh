#!/bin/bash

if [ -e .gitignore ]; then
  echo -n "You already have a .gitignore file in this folder. Do you want to overwrite it? [y/N] "
  read -r answer
  if [ "${answer}" != "y" ]; then
    echo "Aborting due to existing .gitignore file"
    exit
  fi
  echo
fi

echo "Creating new .gitignore file from templates"
printf "# .gitignore generated by make gitignore on %s" "$(date)" > .gitignore

{
  printf '\n\n### MacOS\n'
  curl https://raw.githubusercontent.com/github/gitignore/main/Global/macOS.gitignore
  printf '\n\n### JetBrains\n'
  curl https://raw.githubusercontent.com/github/gitignore/main/Global/JetBrains.gitignore
  printf '\n\n### VS Code\n'
  curl https://raw.githubusercontent.com/github/gitignore/main/Global/VisualStudioCode.gitignore
  printf '\n\n### Python\n'
  curl https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore
} >> .gitignore

if [ -f .gitignore.local ]; then
  printf '\n\n### Project\n' >> .gitignore
  cat .gitignore.local >> .gitignore
fi
