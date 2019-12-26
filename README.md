# The Data Science arXiv

Because you don't want to search for relevant data science articles on [arxiv.com](www.arxiv.com).

## Notes to self
To build a file programmatically:
```
rmarkdown::render('_posts/welcome/welcome.Rmd')
```

Hit problems with pandoc working in RStudio, but not from command line:
https://community.rstudio.com/t/updated-pandoc-now-getting-an-error-when-i-knit-dyld-lazy-symbol-binding-failed/47692

1. https://rdrr.io/cran/rmarkdown/man/pandoc_available.html run `rmarkdown::pandoc_version()` from inside R Studio to check pandoc version.
2. Run it with `R -e "rmarkdown::pandoc_version()"`

I determine i need 2.3.1 because that's what R Studio uses. Download from here: https://github.com/jgm/pandoc/releases/tag/2.3.1. Then things successfully compiled.