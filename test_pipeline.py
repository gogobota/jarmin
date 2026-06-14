import os
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path

class TestJarminPipeline(unittest.TestCase):
    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        self.test_osm = Path(self.work_dir) / "test.osm"
        self.test_pbf = Path(self.work_dir) / "test.osm.pbf"
        
        # Create a minimal OSM XML file for testing the pipeline
        osm_content = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="test">
  <bounds minlat="49.8" minlon="6.0" maxlat="49.82" maxlon="6.02"/>
  <node id="1" lat="49.80" lon="6.00" version="1" changeset="1" timestamp="2026-06-14T00:00:00Z"/>
  <node id="2" lat="49.81" lon="6.01" version="1" changeset="1" timestamp="2026-06-14T00:00:00Z"/>
  <way id="1" version="1" changeset="1" timestamp="2026-06-14T00:00:00Z">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="highway" v="residential"/>
  </way>
</osm>
"""
        self.test_osm.write_text(osm_content)
        
        # Convert minimal XML to PBF using osmium
        subprocess.run(["osmium", "cat", str(self.test_osm), "-o", str(self.test_pbf)], check=True)

    def tearDown(self):
        shutil.rmtree(self.work_dir)

    def test_full_pipeline_bbox(self):
        script_path = Path(__file__).parent / "pipeline.py"
        output_img = Path(self.work_dir) / "output_bbox.img"
        
        cmd = [
            "python3", str(script_path),
            "--bbox", "5.9,49.7,6.1,49.9",
            "--planet-file", str(self.test_pbf),
            "--work-dir", os.path.join(self.work_dir, "work_bbox"),
            "--output", str(output_img),
            "--skip-download"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Bbox Pipeline script failed: {result.stderr}")
        self.assertTrue(output_img.exists(), "Output map file was not generated for bbox")
        self.assertGreater(output_img.stat().st_size, 0, "Output map file is empty for bbox")

    def test_full_pipeline_countries(self):
        script_path = Path(__file__).parent / "pipeline.py"
        output_img = Path(self.work_dir) / "output_countries.img"
        
        # We test providing countries. To avoid relying on live OSM API in tests (which could fail or be slow),
        # we can test the --polygon parameter with a mock geojson generated locally.
        mock_geojson = Path(self.work_dir) / "mock_countries.geojson"
        mock_geojson.write_text("""
        {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "properties": {"name": "MockCountry"},
              "geometry": {
                "type": "Polygon",
                "coordinates": [ [ [5.9, 49.7], [6.1, 49.7], [6.1, 49.9], [5.9, 49.9], [5.9, 49.7] ] ]
              }
            }
          ]
        }
        """)

        cmd = [
            "python3", str(script_path),
            "--polygon", str(mock_geojson),
            "--planet-file", str(self.test_pbf),
            "--work-dir", os.path.join(self.work_dir, "work_countries"),
            "--output", str(output_img),
            "--skip-download"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Polygon Pipeline script failed: {result.stderr}")
        self.assertTrue(output_img.exists(), "Output map file was not generated for polygon")
        self.assertGreater(output_img.stat().st_size, 0, "Output map file is empty for polygon")

    def test_full_pipeline_with_contours(self):
        script_path = Path(__file__).parent / "pipeline.py"
        output_img = Path(self.work_dir) / "output_contours.img"
        contours_pbf = Path(self.work_dir) / "dummy_contours.osm.pbf"
        
        # We can just use the test_pbf as dummy contours since osmconvert doesn't care if the tags actually say "contour"
        shutil.copy(self.test_pbf, contours_pbf)

        cmd = [
            "python3", str(script_path),
            "--bbox", "5.9,49.7,6.1,49.9",
            "--planet-file", str(self.test_pbf),
            "--contours", str(contours_pbf),
            "--work-dir", os.path.join(self.work_dir, "work_contours"),
            "--output", str(output_img),
            "--skip-download"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Pipeline with contours failed: {result.stderr}")
        self.assertTrue(output_img.exists(), "Output map file was not generated for contours test")
        self.assertGreater(output_img.stat().st_size, 0, "Output map file is empty for contours test")

if __name__ == "__main__":
    unittest.main()
