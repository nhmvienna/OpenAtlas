Place
=====

.. toctree::

A place can be e.g. a continent, a city or a graveyard.

.. include:: navigation.rst

Form fields
-----------
* :doc:`/form/name`
* :doc:`/form/alias`
* :doc:`type`
* :doc:`/form/date`
* :doc:`/form/description`
* :doc:`/tools/map`
* **Administrative Unit**
* **Historical Place**
* :doc:`reference_system`

You can edit administrative units and historical places at **Types** in the **Places** tab.

Administrative Unit
*******************
Hierarchy of administrative units in which the place is located, e.g. Austria, Italy and their
respective subunits like Lower Austria, Styria.

Historical Place
****************
Hierarchy of historical places respectively historical administrative units in which the place is
located e.g. Duchy of Bavaria or Lombard Kingdom.

Can be linked via tabs to
-------------------------
* :doc:`source` - when it is referenced there
* :doc:`event` - as an event location
* :doc:`feature` - its subunit
* :doc:`reference`
* :doc:`file`

Places and their subunits
-------------------------
In OpenAtlas a place is a physical thing that has a certain position and/or extend in
space that can be connected to various other information (temporal, spatial, events, sources etc.).
Furthermore, places can be divided into multiple subunits to record archaeological information.
For more information on those subunits see :doc:`feature`, :doc:`stratigraphic_unit`,
:doc:`artifact`, and Human remains as well as a detailed workflow example (:doc:`/examples/archaeological_data`).

An example of a place would be a graveyard. That place is the superior unit. Each grave of this cemetery
is considered a :doc:`feature` that forms the cemetery. Each of those graves is composed of one or many subunits
(:doc:`stratigraphic_unit`). This would be the burials in the very grave (e.g. a primary and a secondary
burial) and the back filling. Each stratigraphic unit may have associated :doc:`artifact` belonging to the
respective unit: e.g. the grave goods of one of the burials, the artifacts found in the back filling. Anthropological information
can be added via :doc:`/entity/human_remains` - another subunit of stratigraphic unit.

.. image:: sub_unit.jpg
