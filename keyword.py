import sublime
import sublime_plugin
import re

from Expression import expression
from Statement import statement
from QuickSearchEnhanced.quick_search import panels
from Context import context
from ProjectFiles.project_files import ProjectFiles

class Keyword():

  def __init__(self, view, type):
    self.view = view
    self.type = type

    settings = self._load_setting()
    if settings == None:
      raise Exception('Unknown type "' + self.type + '"')

    self.place = settings.get('place')
    self.definition = settings.get('definition')
    self.delete = settings.get('delete', 'statement')
    self.cleanup = settings.get('cleanup', None)

    self.new_place = settings.get('new_place', None)
    self.new_place_fallback = settings.get('new_place_fallback', None)
    self.snippets = settings.get('snippets', None)
    self.aliases = settings.get('aliases', None)
    self.search = settings.get('search', None)

  def _load_setting(self):
    result = {}
    for resource in sublime.find_resources('Keyword.sublime-settings'):
      settings = sublime.decode_value(sublime.load_resource(resource))
      if not self.type in settings:
        continue

      result = self._load_settings_dict(result, settings[self.type])

    view_settings = self.view.settings().get('keyword.' + self.type, {})
    result = self._load_settings_dict(result, view_settings)

    return result

  def _load_settings_dict(self, settings, new_settings):
    for value_key in new_settings:
      if value_key == 'aliases':
        if 'aliases' not in settings:
          settings['aliases'] = {}

        settings['aliases'].update(new_settings[value_key])
      else:
        settings[value_key] = new_settings[value_key]

    return settings

  def get_type(self):
    return self.type

  def get_places(self):
    result = []

    matches, _, _ = expression.find(self.view, 0, self.place)
    for match in matches:
      result.append({
        'range': [match.start(0), match.end(0)],
        'value': match.group(0),
      })

    return result

  def get(self, keyword = None, places = None):
    if places == None:
      places = self.get_places()

    result = []
    for place in places:
      shift = place['range'][0]
      matches, _, _ = expression.find(self.view, place['range'][0],
        self.definition, {'range': place['range']})

      for match in matches:
        current = {
          'place': place,
          'range': [shift + match.start(1), shift + match.end(1)],
          'value': match.group(1),
        }

        result.append(current)

        if keyword != None and match.group(1) == keyword:
          return current

    if keyword != None:
      return None

    return result

  def get_delete_region(self, keyword):
    if not isinstance(keyword, dict):
      keyword = self.get(keyword)

    if keyword == None:
      return None

    if self.delete == None or self.delete == 'statement':
      container = statement.get_statement(self.view, keyword['range'])
      result = sublime.Region(*container)
    elif self.delete == 'token':
      result = statement.get_token_delete_region(self.view, keyword['range'][0])
    else:
      raise Exception('Unknown delete type "' + self.delete + '"')

    if self.cleanup != None:
      remained = self.get(places = [keyword['place']])
      if len(remained) == 1:
        place_point = keyword['place']['range'][0]
        container = statement.get_statement(self.view, place_point)
        if container == None:
          return

        result = sublime.Region(*container)
        line = self.view.line(place_point)
        if result.begin() == line.begin() and result.end() == line.end():
          result = sublime.Region(result.begin(), result.end() + 1)

    return result

  def get_insert_info(self, view_or_snippet_index, keyword = None):
    keywords = self.get()
    extra = None
    if len(keywords) == 0:
      if self.new_place == None:
        return None

      _, result, _ = expression.find(self.view, 0, self.new_place)

      fallback = self.new_place_fallback
      if result == None and fallback != None:
        self.view.run_command(fallback['command'], fallback['args'])
        _, result, _ = expression.find(self.view, 0, self.new_place)

      if result == None:
        return None
    else:
      last_keyword = keywords[len(keywords) - 1]
      point = last_keyword['range'][0]

      container = statement.get_statement(self.view, point)
      if container == None:
        return None

      line = self.view.line(container[0])
      result = line.end() + 1

    snippets = self._get_snippets(view_or_snippet_index, keyword)
    if snippets == None or self._is_definition_exist(snippets):
      return None

    return result, snippets

  def _is_definition_exist(self, snippets, places = None):
    for snippet in snippets:
      definition = re.escape(snippet['contents'])

      if places == None:
        places = self.get_places()

      for place in places:
        shift = place['range'][0]
        match = expression.find_match(self.view, place['range'][0],
          definition, {'range': place['range']})

        if match != None:
          return True

    return False

  def _get_snippets(self, view_or_snippet_index, keyword):
    snippet = None
    if isinstance(view_or_snippet_index, int):
      if view_or_snippet_index > len(self.snippets) - 1:
        raise Exception('Unknown snippet with index "' +
          str(view_or_snippet_index) + '" for keyword type "' + self.type)

      snippet = self.snippets[view_or_snippet_index]
    else:
      for current in reversed(self.snippets):
        context_found = (
          not isinstance(view_or_snippet_index, sublime.View) or
          'context' not in current or
          context.check(view_or_snippet_index, current['context'])
        )

        if not context_found:
          continue

        snippet = current
        break

    if snippet == None:
      return None

    snippets = []
    if keyword in self.aliases:
      aliases = self.aliases[keyword]
      if not isinstance(aliases, list):
        aliases = [aliases]

      for alias in aliases:
        new = snippet.copy()
        new['contents'] = self._prepare_snippet_contents(alias,
          keyword)

        snippets.append(new)
    else:
      snippet = snippet.copy()
      snippet['contents'] = self._prepare_snippet_contents(snippet['contents'],
        keyword)
      snippets = [snippet]

    return snippets

  def _prepare_snippet_contents(self, contents, keyword):
    contents = contents.replace('$value', keyword)
    for index, word in enumerate(re.finditer(r'\S+', keyword)):
      contents = contents.replace('$word' + str(index), word.group(0))
    return contents

class Base(sublime_plugin.TextCommand):
  def _show(self, keyword_type, text = '', index = None):
    self.keyword = Keyword(self.view, keyword_type)
    values = self._get_panel_values()

    if len(values) == 0:
      values.append([None, 'No keywords found'])

    panels.create(values, self._open, self._close, self._preview, text,
      [['keyword', self.keyword]], None, index).show()

  def _get_panel_values(self):
    values = []
    for current in self.keyword.get():
      values.append([current, current['value'], current['place']['value'][:30]])

    return values

  def _open(self, panel):
    keyword = panel.get_current_value()
    if keyword == None:
      if len(self.view.sel()) > 0:
        self.view.show(self.view.sel()[0].b)
      return

    point = keyword['range'][0]

    self.view.sel().clear()
    self.view.sel().add(sublime.Region(point, point))
    self.view.show(point)

  def _close(self, panel):
    self.view.erase_regions('keyword')

  def _preview(self, panel):
    keyword = panel.get_current_value()
    if keyword == None:
      return

    self.view.show(keyword['range'][0])
    regions = [sublime.Region(*keyword['range'])]
    self.view.add_regions('keyword', regions, 'string', '')

  def _refresh(self, panel):
    panel.set_values(self._get_panel_values())

  def _create(self, view, position, snippet):
    view.add_regions('keyword', view.sel())

    # placeholder; for some reason spaces are removed from new lines
    view.run_command('insert', {'characters': "P"})

    view.sel().clear()
    view.sel().add(sublime.Region(position, position))
    view.run_command('insert', {'characters': "\n"})

    view.sel().clear()
    view.sel().add(sublime.Region(position, position))
    view.run_command('insert_snippet_enhanced', snippet)

    view.sel().clear()
    view.sel().add_all(view.get_regions('keyword'))
    view.run_command('left_delete')

  def _get_insert_info(self, view_or_snippet_index, text, snippet = None):
    if self.keyword.get(text) != None:
      return

    insert_info = self.keyword.get_insert_info(view_or_snippet_index, text)
    if insert_info == None:
      return None

    position, new_snippet = insert_info
    if snippet == None:
      snippet = new_snippet

    return position, snippet

class ShowKeywords(Base):
  def run(self, edit, keyword_type):
    self._show(keyword_type)

class CreateKeyword(Base):
  def run(self, edit, keyword_type, keyword, snippet = None):
    viewport = self.view.viewport_position()

    self.keyword = Keyword(self.view, keyword_type)
    insert_info = self._get_insert_info(0, keyword, snippet)
    if insert_info == None:
      return

    position, snippets = insert_info
    self._create(self.view, position, snippets[0])
    self.view.set_viewport_position(viewport)

class CreateKeywordAtCursor(Base):
  def run(self, edit, keyword_type):
    if len(self.view.sel()) != 1:
      return

    self.viewport = self.view.viewport_position()

    self.keyword = Keyword(self.view, keyword_type)
    selection = self.view.sel()[0]

    insert_info = self._get_insert_info(selection)
    if insert_info == None:
      return

    self.position, snippets = insert_info
    if len(snippets) == 1:
      self._insert(self.position, snippets[0])
    else:
      values = []
      for snippet in snippets:
        values.append([snippet, snippet['contents']])

      panel = panels.create(values, self._insert_from_panel).show()

  def _insert_from_panel(self, panel):
    self._create(self.view, self.position, panel.get_current_value())

  def _insert(self, position, snippet):
    self._create(self.view, position, snippet)
    self.view.set_viewport_position(self.viewport)

  def _get_insert_info(self, selection):
    if selection.empty():
      selection = self.view.word(selection.b)

    text = self.view.substr(selection)
    if text == '':
      return None

    return super()._get_insert_info(self.view, text)

class CreateKeywordAtList(Base):
  def run(self, edit):
    info = self._get_insert_info()
    if info == None:
      return None

    panel, position, snippet = info
    self._create(panel.get_opener(), position, snippet)
    self._refresh(panel)

  def _get_insert_info(self):
    panel = panels.get_current()
    self.keyword = panel and panel.get_caller('keyword')
    if self.keyword == None:
      return None

    text = panel.get_current_text()
    if text == '':
      return None

    info = super()._get_insert_info(panel.get_panel(), text)
    if info == None:
      return None

    return panel, info[0], info[1]

class DeleteKeywordAtList(Base):
  def run(self, edit):
    panel = panels.get_current()
    self.keyword = panel and panel.get_caller('keyword')
    if self.keyword == None:
      return

    value = panel.get_current_value()
    if value == None:
      return

    region = self.keyword.get_delete_region(value)
    if region == None:
      return

    view = panel.get_opener()
    view.erase(edit, region)

    self._refresh(panel)

class UpdateKeywords(sublime_plugin.TextCommand):
  def run(self, edit, keywords = []):
    self.view.window().run_command('open_file', {'file': '${project}'})
    aliases = self._get_aliases(keywords)
    sublime.set_timeout(lambda: self._write_aliases(aliases), 1000)

  def _get_aliases(self, keywords):
    aliases, searches = {}, {}
    for keyword in keywords:
      searches[keyword] = Keyword(self.view, keyword).search
      aliases[keyword] = {}

    for file_name in ProjectFiles().get():
      file = open(file_name[0])
      try:
        contents = file.read()
      except:
        continue
      finally:
        file.close()

      for keyword in searches:
        expression = searches[keyword]
        for match in re.finditer(expression, contents):
          value, alias = match.group(1), match.group(2)
          if alias not in aliases[keyword]:
            aliases[keyword][alias] = []

          values = aliases[keyword][alias]
          if value not in values:
            values.append(value)

    return aliases

  def _write_aliases(self, aliases):
    view = None
    for current_view in sublime.active_window().views():
      if current_view.file_name().endswith('.sublime-project'):
        view = current_view
        break

    if view == None:
      raise Exception('Project settings not found')

    raw_settings = view.substr(sublime.Region(0, view.size()))
    root_settings = sublime.decode_value(raw_settings)
    if 'settings' not in root_settings:
      root_settings['settings'] = {}

    settings = root_settings['settings']
    for keyword in aliases:
      key = 'keyword.' + keyword
      if key not in settings:
        settings[key] = {}

      if 'aliases' not in settings[key]:
        settings[key]['aliases'] = {}

      settings[key]['aliases'].update(aliases[keyword])

    args = {
      'region': [0, view.size()],
      'text': sublime.encode_value(root_settings)
    }

    view.run_command('replace_region', args)
    view.run_command('pretty_json')
    view.run_command('save')