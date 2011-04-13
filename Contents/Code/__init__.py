import re, string, datetime

VIDEO_PREFIX      = "/video/feedme"
IMAGE_PREFIX      = "/photos/feedme"
AUDIO_PREFIX      = "/music/feedme"


NAMESPACES = {'media':'http://search.yahoo.com/mrss/', 'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd', "itunesB":"http://www.itunes.com/DTDs/Podcast-1.0.dtd"}

FEED_LIST = "feedlist"
# Default feeds
DEFAULT_VIDEO_A = "http://feeds.feedburner.com/ecogeeks"
DEFAULT_VIDEO_B = "http://feeds.feedburner.com/artofthedrink"
DEFAULT_VIDEO_C = "http://feeds.feedburner.com/doctype/episodes"
DEFAULT_VIDEO_D = "http://skyscape.sky.com/skynewsradio/NEWS/dailyheads.xml"

DEFAULT_AUDIO_A = "http://independentstream.podomatic.com/rss2.xml"
DEFAULT_AUDIO_B = "http://feeds.kexp.org/kexp/liveperformances?format=xml"
DEFAULT_AUDIO_C = "http://downloads.bbc.co.uk/podcasts/radio4/film/rss.xml"
DEFAULT_AUDIO_D = "http://www.lonelyplanet.com/podcasts/travelcast.xml"

# directory sites 
BBC_OPML = "http://www.bbc.co.uk/podcasts.opml"

NPR_OPML = "http://podcast.com/opml/npr.opml"
NPR_THUMB = "http://media.npr.org/chrome/news/nprlogo_138x46.gif"
DIGITAL_PODCAST = "http://www.digitalpodcast.com/"
DIGITAL_PODCAST_THUMB = "http://www.digitalpodcast.com/images/newdp465.jpg"
PODCAST_ALLEY = "http://www.podcastalley.com/"
PODCAST_ALLEY_THUMB = "http://static.podcastalley.com/images/podcast_alley_logo2.gif"
PODANZA = "http://www.podanza.com"
PODANZA_THUMB = PODANZA+"/img/logo.gif"
PBS = "http://www.pbs.org"
PBS_THUMB = "http://www.mediabistro.com/fishbowlny/original/pbs-logo.gif"
OPEN_CULTURE = "http://www.openculture.com"
OPEN_CULTURE_THUMB = "http://www.openculture.com/wp-content/themes/openculture_v2c/images/openculture_logo_v2.png"

CACHE_INTERVAL    = 3600

FEED = "feed"
VIDEO = 'video'
AUDIO = 'audio'
IMAGE = 'image'

XPATH_PREDICATE = '[starts-with(@type,"%s")]'

####################################################################################################
def Start():
  PopulateInitialFeedList()
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenuVideo, L("title"), "icon-default.png", "art-default.jpg")
  Plugin.AddPrefixHandler(AUDIO_PREFIX, MainMenuAudio, L("title"), "icon-default.png", "art-default.jpg")
  
  # Leave images out for now. Most photo blogs I've tried don't follow the same rules as video and audio. Bit
  # more freeform, text like, so harder to parse consistently. 
  #Plugin.AddPrefixHandler(IMAGE_PREFIX, MainMenuImages, "My RSS", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.art = R('art-default.jpg')
  DirectoryItem.thumb = R("icon-default.png")
  MediaContainer.title1 = L("title")
  HTTP.CacheTime = CACHE_INTERVAL

####################################################################################################
def PopulateInitialFeedList():
   if not Data.Exists(FEED_LIST):
        feedList = [DEFAULT_VIDEO_A, DEFAULT_VIDEO_B, DEFAULT_VIDEO_C, DEFAULT_VIDEO_D, 
                    DEFAULT_AUDIO_A, DEFAULT_AUDIO_B, DEFAULT_AUDIO_C, DEFAULT_AUDIO_D] 
        Data.SaveObject(FEED_LIST, feedList)

####################################################################################################
def UpdateCache():
    PopulateInitialFeedList()
    if Data.Exists(FEED_LIST):
        feedList = Data.LoadObject(FEED_LIST)
        for feed in feedList:
            HTTP.Request(feed, errors='ignore')
            
####################################################################################################
def MainMenuVideo():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(FeedDisplay, L("video.feeds")), type=VIDEO))
  dir.Append(Function(DirectoryItem(FeedDirectoryList, L("directories"))))
  dir.Append(Function(InputDirectoryItem(AddFeed, title=L("add"), thumb=R("icon-default.png"), prompt=L("add.prompt"))))
  return dir

#########################################################
def MainMenuAudio():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(FeedDisplay, L("audio.feeds")), type=AUDIO))
  dir.Append(Function(DirectoryItem(FeedDirectoryList, L("directories"))))
  dir.Append(Function(InputDirectoryItem(AddFeed, title=L("add"), thumb=R("icon-default.png"), prompt=L("add.prompt"))))
  return dir

#########################################################
# Just a list of feeds for images since directory services
# don't exist
def MainMenuImages():
  
  dir = MediaContainer()
  menu = ContextMenu(includeStandardItems=False)
  menu.Append(Function(DirectoryItem(RemoveFeed, title=L("remove"))))
  dir = MediaContainer(viewGroup='Details', contextMenu=menu)
  
  if not Data.Exists(FEED_LIST):
      PopulateInitialFeedList()
  feedList = Data.LoadObject(FEED_LIST)
  for feed in feedList:
     if ContainsType(feed, IMAGE):
         title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
         thumb = ChannelThumbnail(feed)
         description = ChannelDescription(feed)
         dir.Append(Function(DirectoryItem(RssFeedItems, title=title, summary=description, thumb=thumb, contextKey=feed, contextArgs={}), type=IMAGE, feed=feed, feedThumbnail=thumb))
  
  return dir

#########################################################################
# Faster way of doing this?
# When should this get called and is this what we need?
def CreateCategories():
  feedList = Data.LoadObject(FEED_LIST)
  for feed in feedList:
     if ContainsType(feed, type):
         title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
         categories = []
         for item in XML.ElementFromURL(feed).xpath('//channel/itunes:category', namespaces=NAMESPACES):
             category = item.get('text')
             if category != None and len(category) > 0:
                 categories.append(category.strip())
         for item in XML.ElementFromURL(feed).xpath('//channel/itunesB:category', namespaces=NAMESPACES):
             category = item.get('text')
             if category != None and len(category) > 0:
                 categories.append(category.strip())
              
         if len(categories) == 0:
             categories.append(L("uncategorized"))
         for category in categories:
             if not Dict.HasKey(category):
                 categoryFeeds = dict()
                 Dict.Set(category, categoryFeeds)
             categoryFeeds = Dict.get(category)
             categoryFeeds[title] = feed



#########################################################################
# TODO: list or categories depending on user preference
def FeedDisplay(sender, type):
    return FeedList(sender, type)

#########################################################################
# Categorize a feed
def CategorizeFeed(feed):
    title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
    categories = []
    for item in XML.ElementFromURL(feed).xpath('//channel/itunes:category', namespaces=NAMESPACES):
        category = item.get('text')
        if category != None and len(category) > 0:
            categories.append(category.strip())
    for item in XML.ElementFromURL(feed).xpath('//channel/itunesB:category', namespaces=NAMESPACES):
        category = item.get('text')
        if category != None and len(category) > 0:
            categories.append(category.strip())
              
    if len(categories) == 0:
        categories.append(L("uncategorized"))
    for category in categories:
        if not Dict.HasKey(category):
            categoryFeeds = dict()
            Dict.Set(category, categoryFeeds)
        categoryFeeds = Dict.get(category)
        categoryFeeds[title] = feed
             
#########################################################################
def FeedCategories(sender, type):
  dir = MediaContainer()
  # TODO: category list from the Dict somehow?
  #categories = categoryMap.keys()[:]
  #categories.sort()
  #for category in categories:
  #    feeds = categoryMap[category]
  #    dir.Append(Function(DirectoryItem(CategoryList, title=category), feedMap=feeds, type=type))
  return dir
   
#########################################################
def CategoryList(sender, feedMap, type):
  menu = ContextMenu(includeStandardItems=False)
  menu.Append(Function(DirectoryItem(RemoveFeed, title=L("remove"))))
  dir = MediaContainer(viewGroup='Details', contextMenu=menu)
  
  feedList = feedMap.keys()[:]
  feedList.sort()
  for feedName in feedList:
     feed = feedMap[feedName]
     title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
     thumb = ChannelThumbnail(feed)
     description = ChannelDescription(feed)
     dir.Append(Function(DirectoryItem(RssFeedItems, title=title, summary=description, thumb=thumb, contextKey=feed, contextArgs={}), type=type, feed=feed, feedThumbnail=thumb))
  return dir
  
#########################################################
# Uncategorized list sorted by title
def FeedList(sender, type):
  menu = ContextMenu(includeStandardItems=False)
  menu.Append(Function(DirectoryItem(RemoveFeed, title=L("remove"))))
  dir = MediaContainer(viewGroup='Details', contextMenu=menu, noCache=True)
  
  feedList = Data.LoadObject(FEED_LIST)
  feedMap = dict()
  for feed in feedList:
     if ContainsType(feed, type):
         title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
         feedMap[title] = feed
  
  feedList = feedMap.keys()[:]
  feedList.sort()
  for feedName in feedList:
     feed = feedMap[feedName]
     title = XML.ElementFromURL(feed).xpath('//channel/title')[0].text
     thumb = ChannelThumbnail(feed)
     description = ChannelDescription(feed)
     dir.Append(Function(DirectoryItem(RssFeedItems, title=title, summary=description, thumb=thumb, contextKey=feed, contextArgs={}), type=type, feed=feed, feedThumbnail=thumb))
  
  return dir
  
#########################################################
def ChannelDescription(feed):
    description = ""
    if len(XML.ElementFromURL(feed).xpath('//channel/description')) > 0:
        description = XML.ElementFromURL(feed).xpath('//channel/description')[0].text
    if description == None:
        description = ""
    description = String.StripTags(description.strip())
    return description
  
#########################################################
def ChannelThumbnail(feed):
    thumb = None
    itunesImages = XML.ElementFromURL(feed).xpath('//channel/itunes:image', namespaces=NAMESPACES)
    if len(itunesImages) == 0:
        itunesImages = XML.ElementFromURL(feed).xpath('//channel/itunesB:image', namespaces=NAMESPACES)
    images = XML.ElementFromURL(feed).xpath('//channel/image/url')
    thumbnails = XML.ElementFromURL(feed).xpath('//channel/media:thumbnail', namespaces=NAMESPACES)
    if len(itunesImages) > 0:
        thumb = itunesImages[0].get('href')
    if thumb == None and len(images) > 0:
        thumb = images[0].text
    if thumb == None and len(thumbnails) > 0:
        thumb = thumbnails[0].get('url')
    
    return thumb

#########################################################
def AddFeed(sender, query):
    if query.startswith('feed://'):
        query = query.replace('feed://', 'http://')
    
    feedList = Data.LoadObject(FEED_LIST)
    if query not in feedList:
        if ValidateFeed(query):
            feedList.append(query)
            Data.SaveObject(FEED_LIST, feedList)
            audio = ContainsType(query, AUDIO)
            video = ContainsType(query, VIDEO)
            message = L("success")
            if audio and video:
                message = message + L("both")
            elif audio:
                message = message + L("audio")
            elif video:
                message = message + L("video")
            return MessageContainer(L("added"), message)
        else:
            return MessageContainer(L("invalid"), L("invalid.msg"))
    else:
        return MessageContainer(L("duplicate"), L("duplicate.msg"))
    

#########################################################
def RemoveFeed(sender, key, **kwargs):
    feedList = Data.LoadObject(FEED_LIST)
    feedList.remove(key)
    Data.SaveObject(FEED_LIST, feedList)
    
#########################################################
# Very loose feed validation: 
#    it has to have a title.
#    it has to contain some media items
# 
def ValidateFeed(feedUrl):
    try:
        titleItems = XML.ElementFromURL(feedUrl).xpath('//channel/title')
        if len(titleItems) == 0:
            return False
        for type in [VIDEO, AUDIO, IMAGE]:
            xpathPredicate = XPATH_PREDICATE % type
            if len(XML.ElementFromURL(feedUrl).xpath('//enclosure'+xpathPredicate)) > 0:
                return True
            if len(XML.ElementFromURL(feedUrl).xpath('//media:content'+xpathPredicate, namespaces=NAMESPACES)) > 0:
                return True
    except:
        return False
    
#########################################################
def ContainsType(feed, type):
    try:
        if XML.ElementFromURL(feed) == None:
            return False
    
        xpathPredicate = XPATH_PREDICATE % type
        if len(XML.ElementFromURL(feed).xpath('//enclosure'+xpathPredicate)) > 0:
            return True
        elif len(XML.ElementFromURL(feed).xpath('//media:content'+xpathPredicate, namespaces=NAMESPACES)) > 0:
            return True
        else:
            return False
    
    except:
        return False

#########################################################
def RssFeedItems(sender, feed, type, feedThumbnail):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle, noCache=True)
    for item in XML.ElementFromURL(feed).xpath('//item'):
        title = item.xpath('title')[0].text
        thumb = ItemThumbnail(item)
        if thumb == None:
            thumb = feedThumbnail
                
        subtitle = None
        if len(item.xpath('pubDate')) > 0:
            subtitle = Datetime.ParseDate(item.xpath('pubDate')[0].text).strftime('%a %b %d, %Y')
            
        duration = ItemDuration(item)
        description = ItemDescription(item)
                
        # Deals with multiple representations of the same source. Finds and keeps the first
        # of the required type it comes across. Other logic needed? All I've seen is different
        # codecs of the same source but since Plex can deal with all this should be ok
        # 
        media = None
        xpathPredicate = XPATH_PREDICATE % type
        enclosures = item.xpath('enclosure'+xpathPredicate)
        if len(enclosures) > 0:
            media = enclosures[0].get('url')
        if media == None:
            content = item.xpath('.//media:content'+xpathPredicate, namespaces=NAMESPACES)
            if len(content) > 0:
                media = content[0].get('url')
        
        if media != None:
            if type == VIDEO:
                dir.Append(VideoItem(media, title=title, subtitle=subtitle, summary=description, thumb=thumb, duration=duration))
            elif type == AUDIO:
                dir.Append(TrackItem(media, title=title, subtitle=subtitle, summary=description, thumb=thumb, duration=duration))
            elif type == IMAGE:
                dir.Append(PhotoItem(media, title=title, subtitle=subtitle, summary=description, thumb=media))
                
    return dir

#########################################################
def ItemDuration(item):
    durationStr = None
    if len(item.xpath("itunes:duration", namespaces=NAMESPACES)) > 0:
        durationStr = item.xpath("itunes:duration", namespaces=NAMESPACES)[0].text
    if durationStr == None and len(item.xpath("itunesB:duration", namespaces=NAMESPACES)) > 0:
        durationStr = item.xpath("itunesB:duration", namespaces=NAMESPACES)[0].text
    return ConvertDurationString(durationStr)

#########################################################
def ConvertDurationString(durationStr):
    if durationStr == None:
        return None
    try:
        tokens = durationStr.split(":")
        if len(tokens) == 0:
            return None
        secs = int(tokens[-1])
        mins = 0
        hrs = 0
        if len(tokens) > 1:
            mins = int(tokens[-2])
        if len(tokens) > 2:
            hrs = int(tokens[-3])
        return 1000 * (secs + 60*mins + 60*60*hrs)
    except:
        return None

#########################################################
def ItemDescription(item):
    description = ""
    if len(item.xpath('description')) > 0:
        description = item.xpath('description')[0].text
    if description == None:
        description = ""
    description = String.StripTags(description.strip())
    return description
    
#########################################################
def ItemThumbnail(item):
    thumb = None
    itunesImages = item.xpath('itunes:image', namespaces=NAMESPACES)
    if len(itunesImages) == 0:
        itunesImages = item.xpath('itunesB:image', namespaces=NAMESPACES)
    thumbnails = item.xpath('media:thumbnail', namespaces=NAMESPACES)
    if len(thumbnails) == 0:
        thumbnails = item.xpath('media:content/media:thumbnail', namespaces=NAMESPACES)
    if thumb == None and len(itunesImages) > 0:
        thumb = itunesImages[0].get('href')
    if thumb == None and len(thumbnails) > 0:
        thumb = thumbnails[0].get('url')
    if thumb == None and len(item.xpath('description')) > 0:
        description = item.xpath('description')[0].text
        if description != None:
            items = HTML.ElementFromString(description).xpath('//img')
            if len(items) > 0:
                thumb = items[0].get('src')
    return thumb


#########################################################
def FeedDirectoryList(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(BBCPodcast, "BBC Podcasts", thumb=R("bbc-logo.jpg"))))
  dir.Append(Function(DirectoryItem(DigitalPodcast, "Digital Podcast", thumb=DIGITAL_PODCAST_THUMB)))
  dir.Append(Function(DirectoryItem(NPRPodcasts, "NPR Podcasts", thumb=NPR_THUMB)))
  dir.Append(Function(DirectoryItem(OpenCulture, "Open Culture", thumb=OPEN_CULTURE_THUMB)))
  dir.Append(Function(DirectoryItem(PBSPodcasts, "PBS Podcasts", thumb=PBS_THUMB)))
#  dir.Append(Function(DirectoryItem(Podanza, "Podanza", thumb=PODANZA_THUMB)))
  dir.Append(Function(DirectoryItem(PodcastAlley, "Podcast Alley", thumb=PODCAST_ALLEY_THUMB)))
  return dir


#########################################################
# BBC OPML Feed
def BBCPodcast(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  for item in XML.ElementFromURL(BBC_OPML, encoding='ISO-8859-1').xpath('/opml/body/outline/outline'):
      title = item.get('fullname')
      name = item.get('text')
      if len(item.xpath("outline")) > 0:
          dir.Append(Function(DirectoryItem(BBCStationList, String.StripTags(title), thumb=R("bbc-logo.jpg")), name=name))
  return dir

#########################################################
def BBCStationList(sender, name):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  stationItem = XML.ElementFromURL(BBC_OPML, encoding='ISO-8859-1').xpath('/opml/body/outline/outline[@text="'+name+'"]')[0]
  for program in stationItem.xpath('./outline'):
      title = program.get('text')
      thumb = program.get('imageHref')
      summary = program.get('description')
      feed = program.get('xmlUrl')
      dir.Append(Function(PopupDirectoryItem(OPMLAdd, title, thumb=thumb, summary=summary), feed=feed))
  return dir
 
#########################################################
# NPR OPML Feed
def NPRPodcasts(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for item in XML.ElementFromURL(NPR_OPML).xpath('/opml/body/outline'):
      title = item.get('text')
      dir.Append(Function(DirectoryItem(NPRSubCategories, String.StripTags(title), thumb=NPR_THUMB), category=title))
    return dir


#########################################################
def NPRSubCategories(sender, category):
    dir = MediaContainer(title2=sender.itemTitle)
    categoryItem = XML.ElementFromURL(NPR_OPML).xpath('/opml/body/outline[@text="'+category+'"]')[0]
    for subcategoryItem in categoryItem.xpath('./outline'):
        title = subcategoryItem.get('text')
        if subcategoryItem.get('type') != None:
            url = subcategoryItem.get('xmlUrl')
            dir.Append(Function(PopupDirectoryItem(OPMLAdd, title, thumb=NPR_THUMB), feed=url))
        else:
            dir.Append(Function(DirectoryItem(NPRCategoryList, String.StripTags(title), thumb=NPR_THUMB), category=title))
    return dir

#########################################################
def NPRCategoryList(sender, category):
    dir = MediaContainer(title2=sender.itemTitle)
    categoryItem = XML.ElementFromURL(NPR_OPML).xpath('/opml/body//outline[@text="'+category+'"]')[0]
    for subcategoryItem in categoryItem.xpath('./outline'):
        title = subcategoryItem.get('text')
        url = subcategoryItem.get('xmlUrl')
        dir.Append(Function(PopupDirectoryItem(OPMLAdd, title, thumb=NPR_THUMB), feed=url))
    return dir

#########################################################
# Digital Podcast directory site
def DigitalPodcast(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(DigitalPodcastList, L("newest"), thumb=DIGITAL_PODCAST_THUMB), url=DIGITAL_PODCAST + "opml/digitalpodcastnewnoadult.opml", thumb=DIGITAL_PODCAST_THUMB))
  dir.Append(Function(DirectoryItem(DigitalPodcastList, L("most.viewed"), thumb=DIGITAL_PODCAST_THUMB), url=DIGITAL_PODCAST + "opml/digitalpodcastmostviewednoadult.opml", thumb=DIGITAL_PODCAST_THUMB))
  dir.Append(Function(DirectoryItem(DigitalPodcastList, L("top.rated"), thumb=DIGITAL_PODCAST_THUMB), url=DIGITAL_PODCAST + "opml/digitalpodcasttopratednoadult.opml", thumb=DIGITAL_PODCAST_THUMB))
  dir.Append(Function(DirectoryItem(DigitalPodcastList, L("most.subs"), thumb=DIGITAL_PODCAST_THUMB), url=DIGITAL_PODCAST + "opml/digitalpodcastmostsubscribednoadult.opml", thumb=DIGITAL_PODCAST_THUMB))
  dir.Append(Function(DirectoryItem(DigitalPodcastCategory, L("all.feeds"), thumb=DIGITAL_PODCAST_THUMB), url=DIGITAL_PODCAST + "opml/digitalpodcastnoadult.opml", thumb=DIGITAL_PODCAST_THUMB))
  return dir
  
#########################################################
def DigitalPodcastCategory(sender, url, thumb):
  dir = MediaContainer(title2=sender.itemTitle)
  for item in XML.ElementFromURL(url).xpath('/opml/body/outline'):
      title = item.get('text')
      dir.Append(Function(DirectoryItem(DigitalPodcastCategoryList, title, thumb=thumb), url=url, thumb=thumb, category=title))
  return dir
  
#########################################################
def DigitalPodcastCategoryList(sender, url, thumb, category):
  dir = MediaContainer(title2=sender.itemTitle)
  categoryItem = XML.ElementFromURL(url).xpath('/opml/body/outline[@text="'+category+'"]')[0]
  for item in categoryItem.xpath('outline[@type="rss"]'):
      title = item.get('text')
      url = item.get('url')
      if url == None:
          url = item.get('xmlUrl')
      dir.Append(Function(PopupDirectoryItem(OPMLAdd, title, thumb=thumb), feed=url))
  return dir
  
#########################################################
def DigitalPodcastList(sender, url, thumb):
  dir = MediaContainer(title2=sender.itemTitle)
  for item in XML.ElementFromURL(url).xpath('/opml/body//outline[@type="rss"]'):
      title = item.get('text')
      url = item.get('url')
      if url == None:
          url = item.get('xmlUrl')
      dir.Append(Function(PopupDirectoryItem(OPMLAdd, title, thumb=thumb), feed=url))
  return dir
  
  
#########################################################
def OPMLAdd(sender, feed):
    dir = MediaContainer(title2=sender.itemTitle)
    dir.Append(Function(DirectoryItem(AddFeed, L("add.feed")), query=feed))
    return dir

#########################################################
# Podcast Alley directory site
def PodcastAlley(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    dir.Append(Function(DirectoryItem(PodcastAlleyPage, L("top.50"), thumb=PODCAST_ALLEY_THUMB), pageUrl = PODCAST_ALLEY + "top_podcasts.php?num=50"))
    dir.Append(Function(DirectoryItem(PodcastAlleyCategories, L("browse"), thumb=PODCAST_ALLEY_THUMB)))
    dir.Append(Function(InputDirectoryItem(PodcastAlleySearch, L("search"), prompt=L("search.prompt"), thumb=R('search.png'))))
    return dir
  
def PodcastAlleySearch(sender, query):
    pageUrl = PODCAST_ALLEY + "search.php?searchterm=" + String.Quote(query, True)
    return PodcastAlleyPage(sender, pageUrl)
    
#########################################################
def PodcastAlleyCategories(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for item in XML.ElementFromURL(PODCAST_ALLEY, True).xpath('//form[@name="guideform"]//option[@label]'):
        title= item.get('label')
        path = item.get('value')
        dir.Append(Function(DirectoryItem(PodcastAlleyPage, title, thumb=PODCAST_ALLEY_THUMB), pageUrl = PODCAST_ALLEY+path))
    return dir
    
#########################################################
def PodcastAlleyPage(sender, pageUrl):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    for item in XML.ElementFromURL(pageUrl, True).xpath('//table//tr/td[@class="featuredtextcell"]'):
        summary = String.StripTags(item.text.strip())
        links = item.xpath('.//a[text()="SUBSCRIBE"]')
        if len(links) == 0:
            links = item.xpath('.//a[@class="podcastersub"]')
        if len(links) > 0:
            title = String.StripTags(links[0].get('title'))
            page = links[0].get('href')
            dir.Append(Function(PopupDirectoryItem(PodcastAlleyAdd, title, summary=summary, thumb=PODCAST_ALLEY_THUMB), page=page))
    return dir
  
#########################################################
def PodcastAlleyAdd(sender, page):
    dir = MediaContainer(title2=sender.itemTitle)
    feed = XML.ElementFromURL(PODCAST_ALLEY+page, True).xpath('//td[@class="pod-desc"]//input')[0].get('value')
    dir.Append(Function(DirectoryItem(AddFeed, L("add.feed")), query=feed))
    return dir

#########################################################
# Open Culture directory site
def OpenCulture(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Courses", thumb=OPEN_CULTURE_THUMB), path="/2007/07/freeonlinecourses.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Foreign Language Lessons", thumb=OPEN_CULTURE_THUMB), path="/2006/10/foreign_languag.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Ideas and Culture", thumb=OPEN_CULTURE_THUMB), path="/2006/11/arts_culture_po.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Music", thumb=OPEN_CULTURE_THUMB), path="/2006/09/music_podcast_collection.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Science", thumb=OPEN_CULTURE_THUMB), path="/2007/02/science_podcast-2.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Technology", thumb=OPEN_CULTURE_THUMB), path="/2006/10/technology_podcasts.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Travel", thumb=OPEN_CULTURE_THUMB), path="/2008/01/travel_podcasts.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "University", thumb=OPEN_CULTURE_THUMB), path="/2006/10/university_podc.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Business School", thumb=OPEN_CULTURE_THUMB), path="/2007/02/business_school.html"))
    dir.Append(Function(DirectoryItem(OpenCulturePage, "Law School", thumb=OPEN_CULTURE_THUMB), path="/2007/03/podcasts_from_t.html"))
   
    return dir

#########################################################
def OpenCulturePage(sender, path):
    dir = MediaContainer(title2=sender.itemTitle)
    thumb = OPEN_CULTURE_THUMB
    url = OPEN_CULTURE+path
    for item in XML.ElementFromURL(url, True).xpath('//div[@class="entry"]//ul/li'):
        if len(item.xpath('strong')) > 0:
            title = item.xpath('strong')[0].text
            links = item.xpath('a[text()="Feed"]')
            if title != None and len(title.strip()) > 0 and len(links) == 1:
                feed = links[0].get('href')
                dir.Append(Function(PopupDirectoryItem(AddOpenCulturePodcast, title, thumb=OPEN_CULTURE_THUMB), feed=feed))
    return dir

#########################################################
def AddOpenCulturePodcast(sender, feed):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(AddFeed, L("add.feed")), query=feed))
    return dir

#########################################################
# PBS listing
def PBSPodcasts(sender):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    url = PBS + "/podcasts"
    for categoryItem in XML.ElementFromURL(url, True).xpath('//dl'):
        title = categoryItem.xpath("dt/img")[0].get('title')
        subtitle = categoryItem.xpath('.//em[@class="mediatype"]')[0].text.replace('(','').replace(')','')
        thumb = PBS + categoryItem.xpath("dt/img")[0].get('src')
        description = categoryItem.xpath("dd")[0].text
        feedUrl = categoryItem.xpath('.//input')[0].get('value')
        dir.Append(Function(PopupDirectoryItem(PBSAddPodcastMenu, title=title, subtitle=subtitle, thumb=thumb, summary=description), feedUrl=feedUrl))
    return dir

#########################################################
def PBSAddPodcastMenu(sender, feedUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    dir.Append(Function(DirectoryItem(AddFeed, L("add.feed")), query=feedUrl))
    return dir

#########################################################
# Podanza directory site
def  Podanza(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(PodanzaFeatured, L("featured"), thumb=PODANZA_THUMB)))
  dir.Append(Function(DirectoryItem(PodanzaPopular, L("popular"), thumb=PODANZA_THUMB)))
  dir.Append(Function(DirectoryItem(PodanzaCategories, L("browse"), thumb=PODANZA_THUMB)))
  #dir.Append(Function(InputDirectoryItem(SearchPodanza, "Search Podanza ...", prompt="Enter search term")))
  return dir
  
#########################################################
# Haven't implemented this yet since their web site search always returns nothing
def SearchPodanza(sender, query):
    dir = MediaContainer(title2=sender.itemTitle)
    return dir
    
#########################################################
def PodanzaCategories(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for categoryItem in XML.ElementFromURL(PODANZA, True).xpath('//div[@class="categories"]/ul/li/a'):
      category = categoryItem.text
      categoryUrl = categoryItem.get('href')
      if category != 'Home':
          dir.Append(Function(DirectoryItem(PodanzaCategory, category, thumb=PODANZA_THUMB), categoryUrl=categoryUrl))
    return dir

#########################################################
def PodanzaFeatured(sender):
    url = PODANZA
    itemList = XML.ElementFromURL(url, True).xpath('//ul[@class="podcast-list"]/li')
    return ParsePodanzaList(sender,itemList)
  
#########################################################
def PodanzaPopular(sender):
    url = PODANZA
    itemList = XML.ElementFromURL(url, True).xpath('//ul[@class="podcast-small-list"]/li')
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    for item in itemList:
        title = item.xpath(".//div[@class='podcast-title']/a")[0].text
        thumb = PODANZA + item.xpath(".//div[@class='podcast-image']/a/img")[0].get('src')
        detailsUrl = item.xpath(".//div[@class='podcast-title']/a")[0].get('href')
        dir.Append(Function(PopupDirectoryItem(PodanzaAddPodcastMenu, title=title, thumb=thumb), url=detailsUrl))
    return dir

#########################################################
def PodanzaCategory(sender, categoryUrl):
    
    url = PODANZA + categoryUrl
    itemList = XML.ElementFromURL(url, True).xpath('//ul[@class="podcast-list"]/li')
    return ParsePodanzaList(sender,itemList)
    
#########################################################
def ParsePodanzaList(sender, itemList):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    for item in itemList:
        title = item.xpath(".//div[@class='podcast-title']/a")[0].text
        thumb = PODANZA + item.xpath(".//div[@class='podcast-image']/a/img")[0].get('src')
        description = None
        if len(item.xpath(".//div[@class='podcast-description']")) > 0:
            description = item.xpath(".//div[@class='podcast-description']")[0].text
        detailsUrl = item.xpath(".//div[@class='podcast-actions']/a")[0].get('href')
        dir.Append(Function(PopupDirectoryItem(PodanzaAddPodcastMenu, title=title, summary=description, thumb=thumb), url=detailsUrl))
    return dir
    
#########################################################
def PodanzaAddPodcastMenu(sender, url):
    dir = MediaContainer()
    detailsUrl = PODANZA + url
    podcastUrl = XML.ElementFromURL(detailsUrl, True).xpath('//a[@rel="nofollow"]')[0].get('href')
    dir.Append(Function(DirectoryItem(AddFeed, L("add.feed")), query=podcastUrl))
    return dir
