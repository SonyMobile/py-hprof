// Copyright (C) 2019 Snild Dolkow
// Licensed under the LICENSE.

import android.os.Debug;

import com.example.*;

public class Main {
	public static void main(String[] args) {
		Object shadowing = new Shadowing();
		Object cars = new Cars();
		Object arrays = new Arrays();

		if (args.length > 0) {
			Debug.dumpHprofData(args[0]);
		} else {
			long end = System.currentTimeMillis() + 10000;
			while (System.currentTimeMillis() < end) {
				try {
					Thread.sleep(1000);
				} catch (InterruptedException e) {
				}
			}
		}
	}
}
