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

    def test_full_pipeline(self):
        script_path = Path(__file__).parent / "pipeline.py"
        output_img = Path(self.work_dir) / "output.img"
        
        # We run the pipeline script, feeding it the tiny PBF instead of downloading the massive planet file.
        # Bbox encompasses the test nodes (min_lon,min_lat,max_lon,max_lat)
        cmd = [
            "python3", str(script_path),
            "--bbox", "5.9,49.7,6.1,49.9",
            "--planet-file", str(self.test_pbf),
            "--work-dir", os.path.join(self.work_dir, "work"),
            "--output", str(output_img),
            "--skip-download"
        ]
        
        # Execute the pipeline
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        self.assertEqual(result.returncode, 0, "Pipeline script failed")
        
        # Assert the final map image is generated and is not empty
        self.assertTrue(output_img.exists(), "Output map file was not generated")
        self.assertGreater(output_img.stat().st_size, 0, "Output map file is empty")

if __name__ == "__main__":
    unittest.main()
