---
layout: page
title: Projects
permalink: /projects/
description: This page lists some of my projects
nav_order : 3
nav: true
---

# Internet Measurement Projects

## Validating APNIC's User Estimates

<ul>
  <li><strong>Matt Calder</strong> (Meta)</li>
  <li><strong>Calvin Ardi</strong> (University of Southern California)</li>
  <li><strong>Vasileios Giotsas</strong> (Cloudflare)</li>
  <li><strong>Ethan Katz-Bassett</strong> (Columbia University)</li>
  <li><strong>Todd Arnold</strong> (Army Cyber Institute - West Point)</li>
</ul>

In this project, we investgated the APNIC per-AS user population dataset, which has been widely used but never systematically validated. Our goal was to assess how well APNIC’s user estimates reflect actual Internet usage patterns, and to what extent the dataset can be trusted as a proxy for traffic volume or user distribution.

To do this, we compared APNIC’s data to two independent baselines: broadband subscriber counts across 20 countries and AnonCDN’s measurements of user-agents and traffic volume. Despite some outliers—especially in countries with limited ad reach or unusual network dynamics—we found that APNIC’s estimates generally align with both baselines, particularly for major networks.

However, we also show where APNIC falls short. It can misrepresent countries with limited sampling (e.g., Russia, Myanmar), overrepresent VPNs or mobile-heavy networks, and underestimate cloud/CDN providers. To help users avoid pitfalls, we propose techniques to assess the dataset’s reliability—including checking sample counts, monitoring temporal stability, and cross-validating with public datasets like M-Lab or IXP capacity.

Our broader aim is to provide guidance for researchers and policymakers who rely on APNIC’s dataset. While it’s not perfect, with proper filtering and sanity checks, it offers a surprisingly accurate and globally consistent view of network user populations—making it a valuable, if imperfect, resource for studying Internet infrastructure and access trends.

<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/apnic_comparison.png" title="world_topology" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
  Comparison of Pearson vs. Kendall-Tau correlations between APNIC user estimates and User-Agent counts/traffic volumes from
AnonCDN. The top figure shows User-Agents, while the bottom figure shows traffic volume. Countries are categorized based on their agreement
level in each case. In the User-Agents comparison, most countries exhibit high agreement, particularly in North and South America, Europe,
and Africa. The most significant outliers are found in the African continent showing notably low Kendall-Tau correlations. For traffic volume,
APNIC and AnonCDN datasets closely align in most regions, with the largest discrepancies occurring in South and South Eastern Asia
</div>

**Paper**: <br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&sortby=pubdate&citation_for_view=wfIuIdMAAAAJ:ULOm3_A8WrAC">What's in the Dataset? Unboxing the APNIC per AS User Population Dataset</a><br>

## Squatting on the Internet

<ul>
  <li><strong>Matt Calder</strong> (Meta)</li>
  <li><strong>Italo Cunha</strong> (UFMG)</li>
  <li><strong>Jiangchen Zhu</strong> (Columbia University)</li>
  <li><strong>Ethan Katz-Bassett</strong> (Columbia University)</li>
  <li><strong>Todd Arnold</strong> (Army Cyber Institute - West Point)</li>
</ul>
In this work, we investigate the long-standing but largely opaque practice of IP address squatting—the use of unannounced but allocated IPv4 space by networks that do not own it. We provide the first large-scale public study of this phenomenon, leveraging more than 11 billion traceroutes from Microsoft’s CDN infrastructure, as well as public measurements from RIPE Atlas and Ark.

We begin by identifying a set of /8 IPv4 prefixes historically left unannounced (i.e., potential squat space), and design heuristics to detect and attribute usage of this space to specific networks. We analyze how squat space is used, revealing extensive deployment in CGNAT configurations and by CPE devices, across hundreds of networks. We then examine what happens when this space is suddenly re-announced by its rightful owner (e.g., the U.S. Department of Defense), observing that many squatting networks continue using the space, often routing internally rather than respecting global announcements.

Finally, we assess the risks and distortions introduced by squatting—showing how it can break traceroute-based mapping, introduce routing inconsistencies, and create operational headaches when legitimate announcements return. To help future research, we propose filtering and attribution strategies to identify squat space and mitigate its effects.

**Paper**: <br>
<a href="https://dl.acm.org/doi/10.1145/3594255.3594260">Who Squats IPv4 Addresses?</a><br>


# Geopolitics of the Internet
Inspired by my grandfather, a political activist who took refuge in France, I developed a strong interest in political science. His dream of sparking an intellectual renaissance in a nation shaped by ancient civilization and the pursuit of freedom deeply resonated with me. This led me to mathematical modeling as an efficient tool for abstract reasoning, which became the focus of my first five years at university.

During my undergraduate studies in mathematics, I maintained an interest in the political dynamics of Iran, Russia, and the Black Sea region. A pivotal moment came during a research internship in South Korea, where I discovered the potential of network analysis in understanding political phenomena. This realization shaped my future research: viewing political events through the lens of networks and mathematics.
## Mapping Russian Influence on Twitter

### Collaborators:
<ul>
   <li>Colin Gerard (Geode/French Institute of Geopolitics)</li>
   <li>Guillhem Marotte (Geode/French Institute of Geopolitics)</li>
</ul>
In 2019-2020, I analyzed Russia’s influence on Twitter, developing tools that provided quantitative evidence to support or refute political science hypotheses. I also helped create a standardized methodology for representing graphs, now part of the master of geopolitics program at the University of Paris VIII. Our research revealed instances where Russian influences were erroneously cited in previous French controversies.

<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/methodology_update.png" title="world_topology" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
</div>

**Presentations and conferences:** <br>
<a href="https://connect.apsanet.org/apsa2020/online-program/"> APSA 2020 - Virtual </a>


## Understanding how Iranian Internet evolved to become fully independent and the impact on Iranian's life


### Collaborators:
<ul>
   <li>Kevin Limonier (Geode/French Institute of Geopolitics)</li>
   <li>Louis Petiniaud (Geode)</li>
   <li>Frederick Douzet (Geode/French Institute of Geopolitics)</li>
   <li>Kave Salamatian (University of Savoy)</li>
</ul>
In this project, we show that Iran has leveraged BGP to achieve three specific strategic goals: 1) the pursuit of a self-sustaining national Internet with controlled borders as seemed to have been used in the current events 2) the desire to set up an Iranian Intranet to facilitate censorship which is a passive consequence from the architecture 3) the leverage of connectivity as a tool of regional influence through BGP dependencies. We show that the evolution of the Iranian AS landscape has happened along with a bigger governmental control.
We also note that the Iranian government has been using BGP-tampering for the past few years with increasingly high firepower.
<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/iran_bottleneck.png" title="world_topology" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
  AS-level topology as observed from BGP feeds in 2020.
</div>

The complete shutdown we observe in November 2019 and again in September 2022 are the latest and most massive event of a larger set of BGP related events that Iran that has been witnessed has been for now more than 10 years. We observe that Iran has been able to develop a BGP strategy that enables it to fully control its network without reducing its resilience. We finally note that the Iranian network is connected to the rest of the world through a very number of limited ASes. This leads us to our conclusion that Iran has the potential to completely isolate its network from the rest of the world. This research has led to a paper at the Journal of Cybersecurity and the technical contributions have led to a new approach to perform intelligence through protocol data currently taught at the French Institute of Geopolitics in Paris.

**References in the press**:<br>
 <a href="https://www.lemonde.fr/pixels/article/2019/11/20/internet-coupe-en-iran-le-niveau-de-sophistication-de-ce-blocage-est-une-premiere_6019883_4408996.html">Le Monde</a> <br>
<a href ="https://t.co/rsmSHvLoac">TV5 Monde</a>

**Grants**: <br>
RIPE RACI Grants x 2

**Papers**: <br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:9yKSN-GCB0IC">Measuring the fragmentation of the Internet: the case of the Border Gateway Protocol (BGP) during the Ukrainian crisis</a><br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:d1gkVwhDpl0C">The geopolitics behind the routes data travel: a case study of Iran</a><br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:IjCSPb-OGe4C">Mapping the routes of the Internet for geopolitics: the case of Eastern Ukraine</a><br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:UeHWp8X0CEIC">Le rôle de la topologie d’Internet dans les territoires en conflit en Ukraine, une approche géopolitique du routage des données</a> <br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:Tyk-4Ss8FVUC">Geopolitics of Routing</a>

# Novel ways of measuring topology of the Internet
## Building a manifold representation of private backbones
### Collaborators:
<ul>
   <li>Scott Anderson (University of Wisconsin-Madison)</li>
   <li>Joshua Matthews (University of Wisconsin-Madison)</li>
   <li>Stephen Jasina (University of Wisconsin-Madison)</li>
   <li>Paul Barford (University of Wisconsin-Madison)</li>
   <li>Mark Crovella (Boston University)</li>
   <li>Walter Willinger (Niksun Inc.)</li>
</ul>

You can’t see it, but when you enter something in the search bar, there is a whole network of connections that happens. We typically don’t think about the Internet having a map, but I likened this work to figuring out what the map of the Internet is.

Gradually, cloud and content providers that dominate most of the web have started to build their own networks straight to the user instead of going through multiple different service providers (like Sprint, AT&T, and Verizon) to get to the user. This means most pathways are obscured from being seen. The reasons that service providers obscure their pathways are to protect their equipment, like where their routers are located and what they’re doing, which could open up a host of problems. It also brings a competitive advantage to hiding the relationship between Google and another site, which can be determined through the amount of traffic going from Google to a site.

With these private backbone infrastructures, the standard mapping tool (called traceroute) can no longer be used to evaluate network connectivity on the public web. Companies are able to manipulate traceroute so the information that it’s giving is not completely accurate. Other providers have disallowed traceroute in their networks.

Without traceroute, it’s harder to obtain useful insight into network structures. There is nothing holding companies accountable– they are able to make claims about the performance of their networks without verification from outside sources. It’s also harder for researchers to see what the maps of the internet look like. In order to get around this problem, we came up with a light-weight measurements combined with heavy-weight mathematical analysis tools.

A light-weight analysis tool would be measuring the end-to-end round trip delay (RTT) of information going through the network. RTT can then be augmented in the form of geolocation and path endpoints. Through triangulation, we are able to measure the distance between a user and the router on the map by taking data points that are emitted from different locations. This meant he could geolocate where a router was in the world.

However, there’s not a simple relationship between points on the map and the latency that takes between those points, meaning the distance is not directly predictable by the amount of time it takes to go from one point to another. This means that if a packet (data) is going from a user in Chicago to Denmark, the packet isn’t necessarily going the most direct route.

In addition to this, routes can be curved. What might appear to be a straight line from one node to another may actually be curved– similar to how standing on Earth appears flat, but in reality, is a sphere.

We made an analogy to Einstein’s theory of relativity to come to the conclusion that the distance between nodes might be curved. In order to determine the distance, we used Riemannian geometry– a heavy-weight analysis tool that deals with continuous surfaces. However, most computer science deals with graphs.

Using this mathematical toolkit, we were able to see the paths that packets were taking in different cloud service providers (AWS, Azure, and Amazon). Using the resulting manifold view, we turned the graphs of packets into a map of the world represented with elevation. The points of elevation on the graph show that there are multiple different paths a packet can take. The deeper the valley, the more limited the paths are between two locations.

<center>
<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/updated_manifold_view.jpg" title="world_topology" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
Manifold representation of three large cloud providers
</div>
</center>

We were able to identify that deep valleys between Europe and Asia are because the Red Sea is a choke point for data traffic since cables have to go underwater. Some cloud providers are able to find better routes that go around this chokepoint, such as AWS.

Our research can also help companies determine where to place new infrastructure to help with connectivity issues as was illustrated in our paper. Recently, we were invited to present to the Google Networking group.
<center>
<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/summary_fig.jpg" title="world_topology" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
Our methodology in a nutshell.
</div>
</center>

**Presentations and conferences:** <br>
Google WAN Lab<br>
ACM Sigmetrics 2022 - Virtual

**Papers**: <br>
<a href="https://scholar.google.com/citations?view_op=view_citation&hl=fr&user=wfIuIdMAAAAJ&citation_for_view=wfIuIdMAAAAJ:Y0pCki6q_DkC">Curvature-based Analysis of Network Connectivity in Private Backbone Infrastructures</a><br>
A Manifold View of Connectivity in the Private Backbone Networks of Hyperscalers - in Communications of ACM in August 2023<br>
Matisse: Visualizing Measured Internet Latencies as Manifolds - Under Submission<br>
