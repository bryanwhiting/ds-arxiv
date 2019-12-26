# Todo:

- [x] Get all posts across categories for a week
- [x] Automate the data pull
- [x] Split posts into different days (different topics different days) (30min)
- [x] Add a calendar event (30min)
- [x] Add additional links (25min)
- [x] update the main summaries, simple dates. Wed 12-04. (60)
- [x] update the post formatting: loop through categories, don’t lump them all. (^60)
- [x] format date: (Dec 04, category) bold (Domain/Reuter’s): Title (^60)

- [ ] Add disqus to Arabica - 90?
- [ ] Show categories at the top of arabica
- [ ] move to arabica
- [ ] change the main so it’s Blog, About, and Papers (maybe skip Blog for now since you can easily do About and Papers without having to change the menu bar). (20 min)
- [ ] get running on netlify
- [x] add google analytics (10min)
- [ ] buy domain dsnewsfeed
- [ ] restrict posts to just DS news

- [ ] In the table of contents, put * <a href="#devto">dev.to (15)</a>, which links to <details open id="devto">

- add categories to the bottom of each page? (Why, when you have tags?)
- add disqus (maybe) - does it make sense to have a disqus page? Sharing what you like?
- add sign up page

# Learned:

#### 2018-12-05

I can add this to the top of layouts > index.html to show the categories.
```
{{range ($.Site.GetPage "taxonomyTerm" "categories").Pages }}
   <a href="{{.Permalink}}">{{.Title}}</a></li>
{{end}}
```

I can edit the summary that shows up in layouts > post > single. I can add the date to the tiles

I

Added Google Analytics to the bottom: theme >arabica > layouts > partial > head.html

```
{{ if .Params.ga.async }}
  {{ template "_internal/google_analytics_async.html" . }}
{{ else }}
  {{ template "_internal/google_analytics.html" . }}
{{ end }}
```
