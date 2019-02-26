package com.example.shadowing;

public class ShadowingExample {
	private Object[]  oInstances;
	private Base[]    bInstances;
	private ShadowS[] sInstances;
	private ShadowI[] iInstances;

	public ShadowingExample() {
		sInstances = new ShadowS[] {
			new ShadowS(),
			new ShadowSI(),
			new ShadowSS()
		};

		iInstances = new ShadowI[] {
			new ShadowI(),
			new ShadowII(),
			new ShadowIS()
		};

		bInstances = new Base[7];
		bInstances[0] = new Base();
		System.arraycopy(sInstances, 0, bInstances, 1, 3);
		System.arraycopy(iInstances, 0, bInstances, 4, 3);

		oInstances = new Object[bInstances.length];
		System.arraycopy(bInstances, 0, oInstances, 0, bInstances.length);
	}
}

class Base {
	public static int what = 3;
}

class ShadowS extends Base {
	public static int what = 7;
}

class ShadowSI extends ShadowS {
	public int what = 100;
}

class ShadowSS extends ShadowS {
	public static int what = 103;
}

class ShadowI extends Base {
	public int what = 9;
}

class ShadowII extends ShadowI {
	public int what = 11;
}

class ShadowIS extends ShadowI {
	public static int what = 12;
}
