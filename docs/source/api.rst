.. note:: for internal use only

Bluesfhit API documentation
===========================

Main Entry Functions
--------------------

Blueshift has six defined entry points for user functions as below:

.. function:: initialize(context)

This is the first entry point API function. ``initialize`` is called when
at the beginning of an algorithm run. It also may be called when resuming
a paused algorithm.

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.

User program should utilize this function to set up the algorithm 
initialization (parameters, trading universe, function scheduling, risk 
limits etc).

.. seealso:: :mod:`blueshift.algorithm.context`.

.. function:: before_trading_start(context, data)

This function is called at the beginning of every trading sessions (day). 

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.
    
    ``data(object)``: A data object which can be queried for current or 
    historical data.

User program should utilize this function to set up daily initialization (
e.g. profit and loss, model re-evaluation etc.)

.. seealso:: :mod:`blueshift.data.dataportal`.

.. function:: handle_data(context, data)

This function is called at every clock beat (usually at every minute bar). 
This is the main function that can implement the algorithm logic - how to 
react to the incoming information. 

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.
    
    ``data(object)``: A data object which can be queried for current or 
    historical data.

User program should utilize this function to set up their core algo logic if
the algorithm requires to respond to every trading bar. For algorithm that 
respond at only scheduled events, it is more efficient to use the API function
``schedule_function`` to handle such cases.

.. seealso:: :meth:`blueshift.algorithm.algorithm.TradingAlgorithm.schedule_function`.

.. function:: after_trading_hours(context, data)

This function is called at the end of every session. 

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.
    
    ``data(object)``: A data object which can be queried for current or 
    historical data.

User program should utilize this function to do their end-of-day activities (
e.g. update profit and loss, reconcile, set up for next day).

.. function:: heartbeat(context, data)

This function is called at the same frequency of ``handle_data``, but only
during the non-trading hours. 

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.

User program should ideally not need to implement this. Nevertheless, this 
can have utility in specific cases.

.. function:: analyze(context, data)

This function is called at the end of an algorithm run. This will be called
at the end of period for a backtest. For a live trade, this will may be 
called.

Args:
    ``context(object)``: A container that include the context of the current
    algorithm. This also serves as a place-holder for user defined variables.

User program can implement this method to add custom analysis of backtest 
results (available within the ``context`` variable).


Data API functions
------------------

Below are a list of API functions available for querying asset and data.

.. py:module:: blueshift.data.dataportal
.. automethod:: DataPortal.current

.. py:module:: blueshift.data.dataportal
.. automethod:: DataPortal.history
    

Trading API functions
---------------------

API functions to control trade and algorithm behaviours are follows


Command API functions
---------------------

Below list the API functions available to control the state of an algorithm.
This set of methods are `NOT` available from within the user script. To 
access these functionalities, you need to establish a connection to the 
running algorithm at the ``command channel`` it listens to, and send these
method names (and parameters as json list of dict, respectively for args 
and kwargs) over.

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.pause

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.resume

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.shutdown

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.login

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.refresh_asset_db

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.stop_trading

.. py:module:: blueshift.algorithm.algorithm
.. automethod:: TradingAlgorithm.resume_trading

The current implementation of the ``command channel`` is through ZeroMQ at 
a configurable port. 