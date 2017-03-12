$(document).ready(function(){

    var url = "/dynamic-d3.json";

    var dispatcher = d3.dispatch('jsonLoad');

    $("a").on('click', function() {
        if ((this.href === "https://koirewards.herokuapp.com/") ||
            (this.href === "http://koirewards.herokuapp.com/")) {
           $("#user_d3").remove();
        }
    });

    $(window).on('load',function(){
        if ((window.location.href === "https://koirewards.herokuapp.com/") ||
            (window.location.href === "http://koirewards.herokuapp.com/") ||
            (window.location.href === "data:text/html,chromewebdata")) {
            renderD3(url);
        }
    });

    function renderD3(url) {
    //Constants for the SVG
    var width = 600,
        height = 500;

    //Set up the force layout
    var force = d3.layout.force()
        .gravity(0.09)
        .charge(-140)
        .linkDistance(80)
        .size([width, height]);

    //Append a SVG to the body of the html page. Assign this SVG as an object to svg
    var svg = d3.select("#home-d3-div")
        .append("svg")
        .attr("id", "home_d3")
        .classed("svg-content-responsive", true)
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", "0 0 600 500")
        .attr("width", width)
        .attr("height", height);

    //Set up tooltip
    var tip = d3.tip()
        .attr('class', 'd3-tip')
        .offset([-50, -10])
        .html(function (d) {
        return  d.name + "";
    });
    svg.call(tip);

    // End tooltip

    //-- Insert for pinning
    var node_drag = d3.behavior.drag()
            .on("dragstart", dragstart)
            .on("drag", dragmove)
            .on("dragend", dragend);
        function dragstart(d, i) {
            force.stop(); // stops the force auto positioning before you start dragging
        }
        function dragmove(d, i) {
            d.px += d3.event.dx;
            d.py += d3.event.dy;
            d.x += d3.event.dx;
            d.y += d3.event.dy;
        }
        function dragend(d, i) {
            d.fixed = true; // of course set the node to fixed so the force doesn't include the node in its auto positioning stuff
            force.resume();
        }
        function releasenode(d) {
            d.fixed = false; // of course set the node to fixed so the force doesn't include the node in its auto positioning stuff
            //force.resume();
        }
    //-- End insert for pinning

    //Read the data from JSON 
    d3.json(url, function(error, json) {
        if (error) throw error;

    //Creates the json data structure out of the json data
    force.nodes(json.nodes)
        .links(json.links)
        .start();

    //Create all the line svgs but without locations yet
    var link = svg.selectAll(".link")
        .data(json.links)
        .enter().append("line")
        .attr("class", "link")
        .style("marker-end",  "url(#suit)") //Added 
        ;

    //Do the same with the circles for the nodes - no 
    var node = svg.selectAll(".node")
        .data(json.nodes)
        .enter().append("g")
        .attr("class", "node")
        .call(node_drag) // changed from force.drag for pinning
        .on('mouseover', tip.show) //Added for tooltip
        .on('mouseout', tip.hide) //Added for tooltip
        .on('click', connectedNodes) //Added code for highlighting
        .on('dblclick', releasenode); //Added for pinning

     // Append a circle
  
    node.append("svg:circle")
        .attr("r", function(d) { return Math.sqrt(d.size) / 10 || 4.5; })
        .style("fill", "#eee");

    var images = node.append("image")
        .attr("xlink:href",  function(d) { return d.img;})
        .attr("x", function(d) { return -15;})
        .attr("y", function(d) { return -15;})
        .attr("height", 24)
        .attr("width", 24);

    //Now we are giving the SVGs co-ordinates - the force layout is generating the co-ordinates which this code is using to update the attributes of the SVG elements
    force.on("tick", function () {

        link.attr("x1", function (d) {
            return d.source.x;
        })
            .attr("y1", function (d) {
            return d.source.y;
        })
            .attr("x2", function (d) {
            return d.target.x;
        })
            .attr("y2", function (d) {
            return d.target.y;
        });
        
        node.attr("cx", function(d) {
            return d.x = Math.max(radius, Math.min(width-20 - radius, d.x)); })
            .attr("cy", function(d) {
            return d.y = Math.max(radius, Math.min(height-20 - radius, d.y)); });

        d3.selectAll("circle").attr("cx", function (d) {
            return d.x;
        })
            .attr("cy", function (d) {
            return d.y;
        });

        d3.selectAll("image").attr("x", function (d) {
            return d.x;
        })
            .attr("y", function (d) {
            return d.y;
        });
        
        d3.selectAll("text").attr("x", function (d) {
            return d.x;
        })
            .attr("y", function (d) {
            return d.y;
        });

    });


    //---Insert for arrows-------
    svg.append("defs").selectAll("marker")
        .data(["suit", "licensing", "resolved"])
        .enter().append("marker")
        .attr("id", function(d) { return d; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", 0)
        .attr("markerWidth", 10)
        .attr("markerHeight", 10)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5 L10,0 L0, -5")
        .style("stroke", "#4679BD")
        .style("opacity", "0.9");
    //---End Insert for arrows---

    //--Insert for collision detection--
    var padding = 1, // separation between circles
        radius=8;
    function collide(alpha) {
      var quadtree = d3.geom.quadtree(json.nodes);
      return function(d) {
        var rb = 2*radius + padding,
            nx1 = d.x - rb,
            nx2 = d.x + rb,
            ny1 = d.y - rb,
            ny2 = d.y + rb;
        quadtree.visit(function(quad, x1, y1, x2, y2) {
          if (quad.point && (quad.point !== d)) {
            var x = d.x - quad.point.x,
                y = d.y - quad.point.y,
                l = Math.sqrt(x * x + y * y);
              if (l < rb) {
              l = (l - rb) / l * alpha;
              d.x -= x *= l;
              d.y -= y *= l;
              quad.point.x += x;
              quad.point.y += y;
            }
          }
          return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
        });
      };
    }

    //---End Insert for collision detection---

    //---Insert for highlighting ---
    //Toggle stores whether the highlighting is on
    var toggle = 0;
    //Create an array logging what is connected to what
    var linkedByIndex = {};
    for (i = 0; i < json.nodes.length; i++) {
        linkedByIndex[i + "," + i] = 1;
    }
    json.links.forEach(function (d) {
        linkedByIndex[d.source.index + "," + d.target.index] = 1;
    });
    //This function looks up whether a pair are neighbours
    function neighboring(a, b) {
        return linkedByIndex[a.index + "," + b.index];
    }
    function connectedNodes() {
        if (toggle === 0) {
            //Reduce the opacity of all but the neighbouring nodes
            d = d3.select(this).node().__data__;
            node.style("opacity", function (o) {
                return neighboring(d, o) | neighboring(o, d) ? 1 : 0.1;
            });
            link.style("opacity", function (o) {
                return d.index==o.source.index | d.index==o.target.index ? 1 : 0.1;
            });
            //Reduce the op
            toggle = 1;
        } else {
            //Put them back to opacity=1
            node.style("opacity", 1);
            link.style("opacity", 1);
            toggle = 0;
        }
    }

    //---End Insert for highlighting ---

        });
    }

});