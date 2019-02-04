.. note:: for internal use only

Key Concepts
============

Blueshift is an event-driven research and live trading software. The key 
components of the Blueshift framework are:

Algorithm Modules
+++++++++++++++++
This forms the core of the package. It has three major responsibilities. 

    * Run the big while loop of the event driven framework.
    * Implement all the API interfaces needed from within the input user algo module/ script. 
    * Run and handle all interaction betweem the user module/ script and rest of the framework (like handling communications, managing errors and logs etc.).

Execution Modules
+++++++++++++++++
This modules has two major tasks. 

    * One is to define the interface of the execution environment (the `broker`). The core back-test broker integrated with Blueshift implements this interface. Any broker to we want to integrate with Blueshift must also implements this interface. 
    * The other task is to define clocks that control the execution of the main event loops (implemented in tha Algorithm modules from above).

Data modules
++++++++++++
This modules defines the data interfaces. An implementation of any data 
source will implement this interface.

Asset modules
+++++++++++++
These modules manages the asset definitions. It interfaces with a chosen 
asset database and defines an interface to query that database. This enables
us to refer to a particular asset by its symbol or security id (`sid`). To
extend assets covered by the framework, we need to definite a class for that
particular asset providing a way to store and create that asset with 
desired properties.

Trade modules
+++++++++++++
These modules implements the definitions of trade, order and position 
structures. An `order` is a specification of an intended trade by the 
algorithm. A `trade` is the result of execution of that order. A
`position` is the result of a trade that changes risk exposure to a 
particular asset. An order is uniquely indentified by an order ID. A 
trade is identified by a trade ID and is tied to an order ID. An order 
can have multiple trades. A position is uniquely identified by an asset.

Blotter modules
+++++++++++++++
This implements the double-entry blotter and trade reconciliation system
built in to Blueshift.




