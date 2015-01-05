package: swmm.png metadata.txt SwmmAlgorithmProvider.py SwmmAlgorithm.py __init__.py
	rm -rf qgis_swmm
	mkdir qgis_swmm
	cp $^ qgis_swmm/
	rm -f qgis_swmm.zip
	zip  -r qgis_swmm.zip qgis_swmm
	rm -r qgis_swmm
