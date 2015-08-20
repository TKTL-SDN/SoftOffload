/**
*    Copyright 2015 University of Helsinki
*
*    Licensed under the Apache License, Version 2.0 (the "License"); you may
*    not use this file except in compliance with the License. You may obtain
*    a copy of the License at
*
*         http://www.apache.org/licenses/LICENSE-2.0
*
*    Unless required by applicable law or agreed to in writing, software
*    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
*    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
*    License for the specific language governing permissions and limitations
*    under the License.
**/



// load data for agent table
// ajax not work well with different sources
// here we use some php wrappers

var url = "libs/php/agents-wrapper.php";

// console.log(url);

$.getJSON(url, function(data) {
    $.each(data, function(index, item) {
        //console.log(item);
        var tr = $('<tr></tr>');
        $('<td>'+item.ssid+'</td>').appendTo(tr);
        $('<td>'+item.bssid+'</td>').appendTo(tr);
        $('<td>'+item.clientnum+'</td>').appendTo(tr);
        if (item.client) {
            var clts = '[';
            $.each(item.client, function(i, v) {
                if (clts == '[') {
                    clts += v;
                } else {
                    clts += '<br>' + v;
                }
            });
            if (clts == '[') {
                    clts += ' ';
            }
            $('<td>'+clts+']</td>').appendTo(tr);
        }

        // console.log(tr);
        tr.appendTo('#agent-table');
    });
});

url = "libs/php/uptime.php";
$.getJSON(url, function(data) {
    // console.log(data);
    $('#uptime').html(Math.round(data.systemUptimeMsec / 1000) + ' s');
});