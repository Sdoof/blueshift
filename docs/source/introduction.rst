.. note:: for internal use only

Introduction
============

Blueshift is a flexible, platform agnostic, trading and backtesting framework
for developing systematic investment strategies in Python in a fast and 
reliable way. This makes developing complex (and simple) strategies easy, 
and moving a strategy from back-testing to live trading seamless.

Features
--------

    * Standard and simple APIs: For fast algo development and deployment.
    * Live ready: Seamlessly move from research/backtesting to taking your strategy live
    * Asset agnostic: Can adapt to any asset class you are trading, stocks, FX or cryptos.
    * Full-featured: Comes complete with middle office and back-office functionalities integrated.
    * Fully-loaded: Includies out-of-the-box supports for many live trading platform and data sources.
    * Libraries: Includes a host of useful financial packages, ready to use.
    
.. note::
    
    Blueshift supports Python 3.6 and newer only. We do not have any 
    planned release for earlier versions of Python.    
    
Why Blueshift!
--------------

There are many Pythonic backtesting framework out there. A few are 
excellent for the purpose they were built for. So why another one? The 
issues we found with existing frameworks are:

    * Most are developed for back-testing. Coaxing them in to live trading frameworks is hacky and risky.
    * Many are focussed on specific markets, asset classes or even geographies.
    * Many are suitable only for certain types of strategies (e.g. using a technical indicator to trade).

We developed Blueshift because when we were looking for a framework, we 
found none that meets our requirements. There are quite a few alternatives 
to Blueshift. |zipline| is probably one of the most advanced and 
production-quality platforms out there. It also has a very intuitive user 
interface. In fact, while developing Blueshift, we have attempted to keep 
the API as close to Zipline as possible. Another library, |bt|, uses an 
interesting algo tree concept to integrate multiple strategies. Another 
one of note is |backtrader|. There are many others. A more comprehensive list 
can be found |btlist|.

What it is NOT
--------------

Blueshift is NOT meant for any kind of high-frequency trading (HFT). 
Python is probably not a very suitable platform for HFT. We come from 
a HFT background and are not aware of any Python platform being used 
for HFT execution. Also, if this is news to you, then HFT is probably not
what you need. 

.. warning::

    Backtesting and especially automated trading is far from |ff|. Many
    things can go wrong. While we try our best to catch and highlight 
    such cases by design, our code probably is not completely bug-free. 
    Also there are things beyong control of Blueshift that can go wrong. 
    Like the strategy code going rougue or the datafeed being corrupt or 
    the broker connectivity unstable. Be careful and remember to take 
    appropriate precautions.

.. |zipline| raw:: html

   <a href="https://www.zipline.io/" target="_blank">Zipline</a>
   
.. |bt| raw:: html

   <a href="http://pmorissette.github.io/bt/" target="_blank">bt</a>
   
.. |backtrader| raw:: html

   <a href="https://www.backtrader.com/docu/index.html" target="_blank">backtrader</a>
   
.. |btlist| raw:: html

   <a href="http://statsmage.com/backtesting-frameworks-in-python/" target="_blank">here</a>
   
.. |ff| raw:: html

   <a href="https://en.wikipedia.org/wiki/Fire-and-forget" target="_blank">fire and forget</a>