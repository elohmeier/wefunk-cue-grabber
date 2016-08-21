# wefunk-cue-grabber
creates cue sheets from shows of WEFUNK RADIO

## Dependencies
- python-lxml

## Use cue-sheets with mp3splt
```
for f in $(find -name "*.mp3")
do
mp3splt -o "@b/@N - @p - @t" -c $(basename $f .mp3).cue $f
done
```