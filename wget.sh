#!/bin/bash


wget -r -np -l 1 -nH --cut-dirs=5 -A mp4  \ 
--referer="https://media.talkbank.org/aphasia/English/Protocol/ACWT/PWA/" \  
--header="Cookie: talkbank=s%3A-K8lKGNUAPGr0zgbwd57ikUZgJIuhLmR.Ha9Jxbi%2B%2BhI2u%2FzlO06BoXsPSc7o3ykcbnGBmcNe5LA"  \
--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36" \ 
"https://media.talkbank.org/aphasia/English/Protocol/ACWT/PWA/"

# Example wget command to download each file in the ACWT dir from Talkbank
# Cookie will have to be update with correct login cookie from dev tools
# Referer bypasses CORS policy issues and user agent may not be necessary but is good practice to avoid wget agent blocks



