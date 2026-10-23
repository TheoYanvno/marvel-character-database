# Card photos

Put a character's photo here and it shows on the front of their card and on their profile. Characters without one keep the color card with their initials.

1. Save the image in this folder. Use a `.jpg`, `.png` or `.webp`, ideally portrait (about 3:4) and under 300 KB, e.g. `spider-man.jpg`.
2. In [`data/characters.json`](../../../data/characters.json), add `image` (and optionally `image_credit`) to that character:

   ```json
   {
     "hero_name": "Spider-Man",
     "image": "spider-man.jpg",
     "image_credit": "Photo by …",
     ...
   }
   ```
3. Run `python build_site.py` to update the live demo (it copies the photos in use to `docs/images/`), and `python -m unittest` to check.

The database build checks that every `image` is a plain file name with one of those extensions and that the file is really here. A typo stops the build with the character's name in the message, instead of showing a broken picture.

Only use images you have the right to publish (your own, or ones whose license allows it), and put the credit in `image_credit`.
