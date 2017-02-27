$(document).ready(function(){

    var url = "/custom-d3.json";

    var dispatcher = d3.dispatch('jsonLoad');

    $("a").on('click', function() {
        if (this.href !== "http://localhost:5000/optimize#menu-toggle") {
           $("#user_d3").remove();
        }
    });

    $(window).on('load',function(){
        if ((window.location.href === "http://localhost:5000/optimize") ||
            (window.location.href === "data:text/html,chromewebdata")) {
            renderD3(url);
        }
    });

    function renderD3(url) {
    //Constants for the SVG
    var width = 700,
        height = 350;

    //Set up the force layout
    var force = d3.layout.force()
        .gravity(0.08)
        .charge(-150)
        .linkDistance(90)
        .size([width, height]);

    //Append a SVG to the body of the html page. Assign this SVG as an object to svg
    var svg = d3.select("#d3-div")
        .append("svg")
        .attr("id", "user_d3")
        .classed("svg-content-responsive", true)
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", "0 0 800 400")
        .attr("width", width)
        .attr("height", height);

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
        .on('click', connectedNodes) //Added code for highlighting
        .on('dblclick', releasenode); //Added for pinning

    node.append("image")
        .attr("xlink:href", function(d) { return d.img;})
        .attr("class", "circle")
        .attr("cx", -8)
        .attr("cy", -8)
        .attr("width", 16)
        .attr("height", 16);

    node.append("text")
          .attr("dx", 10)
          .attr("dy", ".35em")
          .text(function(d) { return d.name ;})
          .style("stroke", "gray");
        

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
            return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
            .attr("cy", function(d) {
            return d.y = Math.max(radius, Math.min(height - radius, d.y)); });

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
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5 L10,0 L0, -5")
        .style("stroke", "#4679BD")
        .style("opacity", "0.6");
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

    //--Insert for search ---
    var optArray = [];
    for (var i = 0; i < json.nodes.length - 1; i++) {
        optArray.push(json.nodes[i].name);
    }

    optArray = optArray.sort();

    $(function () {
        $("#search").autocomplete({
            source: optArray
        });
    });

    function searchNode() {

        //find the node

        var selectedVal = document.getElementById('search').value;
        var node = svg.selectAll(".node");

        if (selectedVal == "none") {
            node.style("stroke", "white").style("stroke-width", "1");
        } else {
            var selected = node.filter(function (d, i) {
                return d.name != selectedVal;
            });
            selected.style("opacity", "0");
            var link = svg.selectAll(".link");
            link.style("opacity", "0");
            d3.selectAll(".node, .link").transition()
                .duration(5000)
                .style("opacity", 1);


        }
    }
    });
    // //--End insert for search ---

    function resize() {
      /* Update graph using new width and height (code below) */
    }
     
    d3.select(window).on('resize', resize);

    }

});