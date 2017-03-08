**Welcome to Koi**
===================
### Koi is a webapp that helps its users optimize transfers among their credit card, hotel, and airline reward points.  
> **Note:**

> - User password is hashed upon login via flask.bcrypt.
> - The webapp is by no means a commercial product and does not aim to function as one. 

![Koi Homepage](https://lh3.googleusercontent.com/-TvL6pvy9lnM/WL2-sBoFRGI/AAAAAAAAQaM/oRrKYalmyl8PF8XNiJvCTEJqx_OLp-CzgCLcB/s0/Homepage_vF.png "Homepage_vF.png")
![About Koi](https://lh3.googleusercontent.com/-I9TpDXnqmnI/WMBJbAfEmUI/AAAAAAAAQhY/va8jQdJapNUuEYMOkcUV9eboiMfSVTU0QCLcB/s0/Visualize.png "Visualize.png")
![Contact Us](https://lh3.googleusercontent.com/-FbPIjBSiqYc/WL3BFgwJsrI/AAAAAAAAQao/3iOfm3a9zG0poHRUdeeA5-rWd88dl_93gCLcB/s0/ContactUs.png "ContactUs.png")

![enter image description here](https://lh3.googleusercontent.com/-RDWu8rnRiSg/WMBQnQlBV4I/AAAAAAAAQjI/bWkB9plOczku8e0c3KM49D8ZmZLnb71gQCLcB/s0/demo1.gif "demo1.gif")

![enter image description here](https://lh3.googleusercontent.com/-tkWBTmO8XUs/WMBOg2iNTjI/AAAAAAAAQio/VrT95qvrSXkJ8Hd20OwsZ7yxPNeJVMdrgCLcB/s0/demo2.gif "demo2.gif")
----------

### Navigate

[Welcome to Koi](https://github.com/linvivian7/koi#welcome-to-koi)

* [Overview](https://github.com/linvivian7/koi#koi-is-a-webapp-that-helps-its-users-optimize-transfers-among-their-credit-card-hotel-and-airline-reward-points)

[Navigate](https://github.com/linvivian7/koi#navigate)

[Dashboard](https://github.com/linvivian7/koi#dashboard)

 * [Main](https://github.com/linvivian7/koi#main)
  * [Update Balance](https://github.com/linvivian7/koi#-update-balance--not-shown)
  * [Transfer Points](https://github.com/linvivian7/koi#-transfer-points)
  * [Point Distribution](https://github.com/linvivian7/koi#-point-distribution)
  * [Program Balances](https://github.com/linvivian7/koi#-program-balances)
 * [Optimization UI](https://github.com/linvivian7/koi#optimization)
  * [User Actions](https://github.com/linvivian7/koi#-user-actions)
  * [Visualization](https://github.com/linvivian7/koi#-visualization-of-how-programs-map-to-each-other4)

 * [Optimization Process](https://github.com/linvivian7/koi#optimization-process)
 
[Transaction History](https://github.com/linvivian7/koi#transaction-history)

[Koi History](https://github.com/linvivian7/koi#koi-history)


Dashboard
-------------
Let's explore all the functionalities the dashboard provides for users.

#### Main
![Main Dashboard](https://lh3.googleusercontent.com/-fxwG8ItMq7A/WL3HsHNMOoI/AAAAAAAAQb8/RXHR13kdocIekZe8OeCsAJLj57RGz3c2QCLcB/s0/Dashboard.png "Dashboard.png")

#####$ Update Balance  (not shown)

 - Add/update program balances
 - Editable-select[1] drop-down

 [1]:  https://github.com/indrimuska/jquery-editable-select

#####$ Transfer Points

 - *Transferred From*: List of programs within user portfolio with point conversion 
 - *To*: Dynamic list rendered post-AJAX call to database based on *Transferred From* selection
 - *Ratio*: Ratio between the selected **outgoing** and **receiving** programs
 
 > **Transfer Constraints:**
> - No balances, beginning or ending, can be negative
> - Transfer amounts are full-points

#####$ Point Distribution 

 - Donut Chart rendered via Chart.js
 - Section colors are generated dynamically based on the # of programs and have unique RGB
 - Code inspired by stack **overflow** answer[2]
[2]: http://stackoverflow.com/questions/43044/algorithm-to-randomly-generate-an-aesthetically-pleasing-color-palette
```python
def generate_random_color(ntimes, base=(255, 255, 255)):
    """ Generate random pastel blue-green and red-orange colors for charts """

    colors = set()

    i = 1

    while len(colors) < ntimes + 1:

            if i % 2 == 0:
                red = random.randint(0, 50)
                green = random.randint(150, 170)
                blue = random.randint(155, 219)

            if i % 2 != 0:
                red = random.randint(240, 250)
                green = random.randint(104, 168)
                blue = random.randint(0, 114)

            if base:
                red = (red + base[0]) / 2
                green = (green + base[1]) / 2
                blue = (blue + base[2]) / 2

            color = (red, green, blue)
            colors.add(color)
            i += 1

    return colors

```

#####$ Program Balances 

 - All tables are jQuery datatables[3] 
 - Searchable, sortable, enables column re-order and pagination, and have fixed headers
 - Click <kbd>x</kbd> to delete a program balance

[3]: https://datatables.net/

#### Optimization

![Optimization Page](https://lh3.googleusercontent.com/-dYT2Ivwp7IM/WL3Mqwa6FqI/AAAAAAAAQcM/AwRk__NfMsY8oda9SaNrAOH3uhXZ3IHSgCLcB/s0/Optimize.png "Optimize.png")

#####$ User Actions

 - User selects a **goal program** whose value he/she would like to maximize
 - User inputs a **goal balance** for the goal program 
 - Press <kbd>Run Optimization</kbd>
 - Press <kbd>Yes</kbd> to commit transfers within Koi profile

#####$ Visualization of how programs map to each other[4]

 - _function **renderD3**_ makes AJAX call to server
 - Server returns jsonified mapping for the user's portfolio
 - Full D3 of all programs on Koi can be found in the **Visualize** section of the **Homepage**.
 
 [4]: http://www.coppelia.io/2014/07/an-a-to-z-of-extra-features-for-the-d3-force-layout/

 ![D3 actions](https://lh3.googleusercontent.com/-rjH4WESmjaU/WL3PKX7EcZI/AAAAAAAAQcY/MM07RpWMH0Eef99HTjUAmVpxxn7Tz9TRwCLcB/s0/D3.png "D3.png")
 
#### Optimization Process
![Optimization Process](https://lh3.googleusercontent.com/JbtvzNuV0GWMyk8HjvkVD5OSaFr4S4qBS4Ws7wV6Mb4Cz7vmPw3kp077up3KXaOsyH8qykXs8w=s0 "process.png")

Brief overview of the calculation process. For more information, please see **helper.py**.

#####$ _function **optimize**_  (start)
```python 
def optimize(user_id, source, goal_amount, commit=False):
    """ Optimizes points transfer """
```
	*  source = goal_program

#####$ _function **bellman\_ford**_ [5] returns:

```python 
def bellman_ford(graph, source):
```

```python 
# example_min_cost: [(16, 0), (212, 0.0), (164, 1.0986122886681098), (6, inf), (170, inf), (187, inf)]
# example predecessor: {164: 212, 6: None, 170: None, 16: None, 212: 16, 187: None}
```
 - Array of node-to-cost tuples
 - Hashmap of nodes and predecessors as key, value pairs

[5]: https://gist.github.com/joninvski/701720

#####$ _function **make\_path**_ constructs possibly paths with doubly-linked lists
```python 
def make_path(current, source, predecessor):
```

#####$ _function **is\_route\_possible**_ applies balance ceiling and whole-point transfer constraints
```python 
def is_route_possible(user, goal_amount, node):
    """ Return True or False if path is viable """

    return goal_amount <= balance_capacity(user, node)
```

#####$ _function **optimize**_  (end) returns optimal path with involved programs, transfer amounts, vendor urls, and ratios.


----------


Transaction History
-------------------

Upon update, deletion, transfer, and commitment to optimized transfers, users can view their entire transaction history on their Koi profile. 

![Activity Table](https://lh3.googleusercontent.com/-TYi6x9dHrww/WL3VxlY12-I/AAAAAAAAQc0/AbkXZ4_2N1QIBi_Hq49dMoKjkO7YGHPzgCLcB/s0/Activity.png "Activity.png")

![Transfers Table](https://lh3.googleusercontent.com/-7JAtOGdheb8/WL3WAk6g62I/AAAAAAAAQc8/-lE3QgQpdDcbrJg6ARaT1A9I2Qp0ZNSwgCLcB/s0/Transfers.png "Transfers.png")

----------

Koi History
-------------------

Still here? Walk through the progress of Koi development with us! 

Week 1 

![enter image description here](https://lh3.googleusercontent.com/-1Ue7VCpKFNA/WL3ZTPIgPUI/AAAAAAAAQd4/XNyyFhw7i8YegTQ3YmFb06VBOZMC6Zn7wCLcB/s0/Screenshot+2017-02-13+12.22.31.png "2-13-17_Homepage.png")

![enter image description here](https://lh3.googleusercontent.com/-9CvvjzIuztY/WL3YxrYAGAI/AAAAAAAAQdk/0Z1vas6KLaQVxhdowmzwDN2geb7mvp6twCLcB/s0/ActivityHistory.png "2-13-17_ActivityHistory.png")

Week 2

![enter image description here](https://lh3.googleusercontent.com/-IHXE2zM4Y2g/WL3Zq0Nn5nI/AAAAAAAAQeI/aLklVjSBhZo-F3Nqf4py6diAABhreyQqwCLcB/s0/Screenshot+2017-02-17+02.31.23.png "02-17-17_homepage.png")

Week 3
![enter image description here](https://lh3.googleusercontent.com/-A2fzB7sgD4E/WL3aUv-px8I/AAAAAAAAQeg/AfEJA0XxnLEvtyleBmewMxmeYRS0NiWhwCLcB/s0/Screenshot+2017-02-23+22.03.18.png "2-23-17_visualize.png")

![enter image description here](https://lh3.googleusercontent.com/-oDR4WC0lSNQ/WL3avhYppFI/AAAAAAAAQew/NvcNBOwOuT4zifdlrpKribmqnB4-OLiLACLcB/s0/Screenshot+2017-02-23+22.01.08.png "2-23-17_activity.png")


### Support StackEdit

  [^stackedit]: [StackEdit](https://stackedit.io/) is a full-featured, open-source Markdown editor based on PageDown, the Markdown library used by Stack Overflow and the other Stack Exchange sites.