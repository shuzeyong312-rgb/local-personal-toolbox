# Run manually. This profile is independent of your normal Chrome profile.
$profilePath = Join-Path $PSScriptRoot 'profile'
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' "--user-data-dir=$profilePath" '--remote-debugging-address=127.0.0.1' '--remote-debugging-port=9222' 'https://detail.1688.com/offer/1056305371784.html'
