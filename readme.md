# Sublime Keyword plugin

The glorious keywords manager. Created to manage often-encountered keywords like
"import", "use" and etc. By default support python "import" and php "use".


### Demo

![Demo](https://raw.github.com/shagabutdinov/sublime-keyword/master/demo/demo.gif "Demo")


### Installation

This plugin is part of [sublime-enhanced](http://github.com/shagabutdinov/sublime-enhanced)
plugin set. You can install sublime-enhanced and this plugin will be installed
automatically.

If you would like to install this package separately check "Installing packages
separately" section of [sublime-enhanced](http://github.com/shagabutdinov/sublime-enhanced)
package.


### Features

1. Create keyword from text (e.g. "from os import path" or "use yii\helpers\Url;")

2. Display list of found keywords

3. Delete keyword using list of keywords

4. Create keyword using list of keywords

5. Update aliases from current project to reuse import definitions

This plugin is espesually worthy when using together with snippets
([sublime-snippet-caller](http://github.com/shagabutdinov/sublime-snippet-caller).
E.g. "rs" expands to "re.search($0)" and creates "import re" in beginning of
file in python.

Note that for now it works only with python and php. You should modify settings
and .sublime-keymap files to add support for new languages.


### Usage


##### Insert keyword

  ```
  # before
  re|.search() # <- cursor after "re"

  # after insert keyword
  import re
  re|.search()

  # before
  <p><?= Ht|ml::encode($value) // <- cursor at Html ?>

  # after
  <?php
  use yii\helpers\Html;
  ?>
  <p><?= Html::encode($value) ?>
  ```

##### Insert keyword with snippet

```
# before
rs| # [tab]

# after
import re

re.search(|)
```

##### Snippet example

  ```
  <snippet>
    <content><![CDATA[
  re.search($1, ${2:$indented_selection})
  ]]></content>
    <tabTrigger>rs</tabTrigger>
    <scope>source.python</scope>
    <commands>
      [
        {
          "command": "create_keyword",
          "args": {"keyword_type": "python.import", "keyword": "re"},
        },
        "RUN",
      ]
    </commands>
    <description>re.search</description>
  </snippet>
  ```

### Settings

Settings is hash table; settings can be defined in KeymapEnhanced.sublime-settings
file or in project settings (in this case "keyword" should precede settings key)
each value contains hash table in following format:


##### "place"

Regexp that points to where to insert keywords.


##### "new_place_fallback"

Sublime command that executed if no "place" found.


##### "new_place"

Regexp that points where to insert keywords if no "place" found.


##### "definition"

Regexp that parses single definition from keywords list.


##### "delete"

How to delete keyword (allowed values: "token" or "statement").


##### "cleanup"

Boolean; if true then "delete statement" will be executed after removing last
keyword.


##### "snippets"

Snippets that will be used to create keywords from panel.


##### "search"

Regexp that shows how to search keyword.


##### "aliases"

List of aliases to quickly define keyword.


### Commands

| Description              | Keyboard shortcut |
|--------------------------|-------------------|
| Show keywords            | ctrl+u, ctrl+i    |
| Update project keywords  | ctrl+u, i         |
| Create keyword at cursor | ctrl+alt+e        |
| Delete keyword from list | ctrl+d            |
| Create keyword at list   | ctrl+n            |

| Command paltte                          |
|-----------------------------------------|
| Keyword: Show python imports            |
| Keyword: Show php uses                  |
| Keyword: Update python imports          |
| Keyword: Update php uses                |
| Keyword: Create python import at cursor |
| Keyword: Create php use at cursor       |


### Dependencies

- https://github.com/shagabutdinov/sublime-expression
- https://github.com/shagabutdinov/sublime-statement
- https://github.com/shagabutdinov/sublime-quick-search-enhanced
- https://github.com/shagabutdinov/sublime-context
- https://github.com/shagabutdinov/sublime-project-files