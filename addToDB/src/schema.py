def getSchemaTEST(db_id, params):
  return """{
          "parent": {
            "database_id": \"""" + db_id + """\"
          },
          "properties": {
            "a":  {
  	    		"title": [
  	    			{
  	    				"text": {
  	    					"content": \"""" + params['a'] + """\"
  	    				}
  	    			}
  	    		]
  	    	},
           "b": { "number": 88 }
          }
      }"""



def getSchemaPROv1(db_id, params):
  return """{
  "parent": {
    "type": "database_id",
    "database_id": \"""" + db_id + """\"
  },
  "properties": {
    "T.Sport": {
      "number": """ + params['T.Sport'] + """
    },
    "Expenses": {
      "number": """ + params['Expenses'] + """
    },
    "T.Reading": {
      "number": """ + params['T.Reading'] + """
    },
    "date": {
      "date": {
        "start": \"""" + params['date'] + """\",
        "end": null,
        "time_zone": null
      }
    },
    "T.Projects": {
      "number": """ + params['T.Projects'] + """
    },
    "Tag": {
      "type": "multi_select",
      "multi_select": [
        """ + params['Categories'] + """
      ]
    },
    "T.Learning": {
      "number": """ + params['T.Learning'] + """
    },
    "item": {
      "id": "title",
      "type": "title",
      "title": [
        {
          "type": "text",
          "text": {
            "content": \"""" + params['title'] + """\",
            "link": null
          },
          "annotations": {
            "bold": false,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
          },
          "plain_text": \"""" + params['title'] + """\",
          "href": null
        }
      ]
    }
  }
}
"""