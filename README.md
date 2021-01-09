# Mac Keymappings

Your Mac keycaps probably only have English and perhaps another alphabet on them. But with modifier
keys, you can get some more obscure characters, like the vowel points in Hebrew. You can see these with the
[Keyboard Viewer](https://support.apple.com/en-il/guide/mac-help/mchlp1015/11.0/mac/11.0), accessible from the 
keyboard-changer in the menu at the top of your screen, but that image is small, and does not allow you 
to search for the obscure character that you want.
To see the full keymappings in your keyboard, do this:

1. Follow the [instructions here](https://apple.stackexchange.com/a/410606/351942) for creating a new keyboard layout.
2. File->Save.... Save it as Hebrew, for example.
3. You will need a file with extension _keylayout_, for example, _Hebrew.keylayout_.
4. You may see a directory named "Hebrew.bundle"
5. You cannot just double-click on it, as that would open Ukelele. Instead, right-click, "Open Package Contents".
6. In that directory, navigate to _Contents_/Resources_. There you will find the file with extension _keylayout_, for example, _Hebrew.keylayout_.
7. Copy it to the directory of this project. Rename it to _keylayout.xml_
8. Run _run.sh_.
9. This will generate the HTML output and open it.