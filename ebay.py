import urllib.request
import json
import xml.etree.ElementTree as ET
import sqlite3 as sql
import sys

print('Start of program...');
	
url = 'https://api.sandbox.ebay.com/ws/api.dll'
data_to_send = '''<?xml version="1.0" encoding="utf-8"?>
	<GetCategoriesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
		<RequesterCredentials>
			<eBayAuthToken>AgAAAA**AQAAAA**aAAAAA**PlLuWA**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFk4GlDpaDpAudj6x9nY+seQ**LyoEAA**AAMAAA**wSd/jBCbxJHbYuIfP4ESyC0mHG2Tn4O3v6rO2zmnoVSF614aVDFfLSCkJ5b9wg9nD7rkDzQayiqvwdWeoJkqEpNQx6wjbVQ1pjiIaWdrYRq+dXxxGHlyVd+LqL1oPp/T9PxgaVAuxFXlVMh6wSyoAMRySI6QUzalepa82jSQ/qDaurz40/EIhu6+sizj0mCgjcdamKhp1Jk3Hqmv8FXFnXouQ9Vr0Qt+D1POIFbfEg9ykH1/I2CYkZBMIG+k6Pf00/UujbQdne6HUAu6CSj9wGsqQSAEPIXXvEnVmtU+6U991ZUhPuA/DMFEfVlibvNLBA7Shslp2oTy2T0wlpJN+f/Jle3gurHLIPc6EkEmckEpmSpFEyuBKz+ix4Cf4wYbcUk/Gr3kGdSi20XQGu/ZnJ7Clz4vVak9iJjN99j8lwA2zKW+CBRuHBjZdaUiDctSaADHwfz/x+09bIU9icgpzuOuKooMM5STbt+yJlJZdE3SRZHwilC4dToTQeVhAXA4tFZcDrZFzBmJsoRsJYrCdkJBPeGBub+fqomQYyKt1J0LAQ5Y0FQxLHBIp0cRZTPAuL/MNxQ/UXcxQTXjoCSdZd7B55f0UapU3EsqetEFvIMPxCPJ63YahVprODDva9Kz/Htm3piKyWzuCXfeu3siJvHuOVyx7Q4wyHrIyiJDNz5b9ABAKKauxDP32uqD7jqDzsVLH11/imKLLdl0U5PN+FP30XAQGBAFkHf+pAvOFLrdDTSjT3oQhFRzRPzLWkFg</eBayAuthToken>
		</RequesterCredentials>
		<DetailLevel>ReturnAll</DetailLevel>
	</GetCategoriesRequest>'''
ns = {'d': 'urn:ebay:apis:eBLBaseComponents'};

def getEbayCategories():
	print("Getting categories..")
	values = {'data' : data_to_send	}
	headers = { "Content-Type": "text/xml",
			#"X-EBAY-API-DETAIL-LEVEL": "0",
			"X-EBAY-API-CALL-NAME" : "GetCategories"
			,"X-EBAY-API-APP-NAME": "EchoBay62-5538-466c-b43b-662768d6841"
			,"X-EBAY-API-CERT-NAME": "00dd08ab-2082-4e3c-9518-5f4298f296db"
			,"X-EBAY-API-DEV-NAME": "16a26b1b-26cf-442d-906d-597b60c41c19"
			,"X-EBAY-API-SITEID": "0"
			,"X-EBAY-API-COMPATIBILITY-LEVEL": "861"			
			}
	
	print("Got categories....")
	req = urllib.request.Request(url, data = None, headers = headers)
	req.data = data_to_send.encode();
	res =  urllib.request.urlopen(req);
	
	#print("After request....")
	res_data = res.read();
	return res_data;

def parseEbayCategories(res_data):	
	print("Extracting categories...")
	root = ET.fromstring(res_data);
	results = root.findall('d:CategoryArray/d:Category',namespaces=ns);
	return results;
	
def createDB(db_file):
	print("Creating DB....");
	try:
		conn = sql.connect(db_file);
		c = conn.cursor();
		c.execute('''CREATE TABLE categories
             (catid integer NOT NULL PRIMARY KEY, parentid integer, name text, level integer, bestoffer integer,
			 FOREIGN KEY (parentid) REFERENCES category (catid))''');
		#c.execute('''
		#	 CREATE VIRTUAL TABLE categories_closure USING transitive_closure (
		#	 tablename="categories", idcolumn="catid", parentcolumn="parentid");''');
			 
		conn.commit();
	except sql.Error as e:
		print(e);
	finally:
		conn.close();

def populateDB(db_file, data):
	print("Populating DB...")
	try:
		conn = sql.connect(db_file);
		c = conn.cursor();
		for cat in data:
			catid = int(cat.find('d:CategoryID',ns).text);
			parentid = int(cat.find('d:CategoryParentID',ns).text);
			parentid = parentid if ( parentid != catid) else None;
			name = str(cat.find('d:CategoryName',ns).text);
			level = int(cat.find('d:CategoryLevel',ns).text);
			bestoffer = 1 if (cat.find('d:BestOfferEnabled',ns) is not None and cat.find('d:BestOfferEnabled',ns).text == "true") else 0;
			
			sql_stmt = "INSERT INTO categories VALUES (?, ?, ?, ?, ?)";
			c.execute(sql_stmt, (catid, parentid, name, level, bestoffer) );
			conn.commit();
			
	except sql.Error as e:
		print(e);
	finally:
		conn.close();
	
def dropDB(db_file):
	print("Dropping DB...")
	try:
		conn = sql.connect(db_file);
		c = conn.cursor();

		c.execute('''DROP TABLE IF EXISTS categories''')
	except sql.Error as e:
		print(e);
	finally:
		conn.close();

def renderCategoryTree(file, level, cat_id, cursor):
	
	if level == 6:
		return;
		
	file.write("<ul>")
	sql_stmt = "SELECT * FROM categories WHERE parentid = ?";
	cursor.execute(sql_stmt, (int(cat_id),) );
	results = cursor.fetchall();
	for row in results:
			file.write("<li>"+ row[2]);
			renderCategoryTree(file, level+1, row[0], cursor)
			file.write("</li>");
	file.write("</ul>");
	
def renderCategory(db_file, cat_id):
	print("Rendering " + cat_id);
	try:
		conn = sql.connect(db_file);
		c = conn.cursor();
		sql_stmt = """SELECT * FROM categories WHERE catid = ?""";
		c.execute(sql_stmt, (int(cat_id),) );
		results = c.fetchone();
		if results is None:
			print("No category with id " + cat_id);
			return;
		#create_file
		f = open(str(cat_id)+".html","w+");
		f.write("<html>") 
		f.write("<p>"+results[2]+"</p>");
		level = results[3];
		
		renderCategoryTree(f, level, cat_id, c);
				
		f.write("</html>");
		f.close();
	except sql.Error as e:
		print(e);
	finally:
		conn.close();
	
if (len(sys.argv) == 2 and sys.argv[1] == '--rebuild'):
	print("Rebuilding...");
	dropDB("C:\\Users\\user\\sqlite_databases\\ebay.db");
	createDB("C:\\Users\\user\\sqlite_databases\\ebay.db");
	
	res_data = getEbayCategories();
	categories = parseEbayCategories(res_data);
	populateDB("C:\\Users\\user\\sqlite_databases\\ebay.db", categories);
elif (len(sys.argv) == 3 and sys.argv[1] == '--render'):
	print("Rendering...");
	renderCategory("C:\\Users\\user\\sqlite_databases\\ebay.db", sys.argv[2]);
	

