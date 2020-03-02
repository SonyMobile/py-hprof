package com.example;

public class Shadowing {
	private Object[]  objects   = new Object[7];
	private Base[]    bases     = new Base[7];
	private ShadowI[] instances = new ShadowI[3];
	private ShadowS[] statics   = new ShadowS[3];

	public Shadowing() {
		objects[0] = bases[0] = new Base();
		objects[1] = bases[1] = instances[0] = new ShadowI();
		objects[2] = bases[2] = instances[1] = new ShadowII();
		objects[3] = bases[3] = instances[2] = new ShadowIS();
		objects[4] = bases[4] =   statics[0] = new ShadowS();
		objects[5] = bases[5] =   statics[1] = new ShadowSI();
		objects[6] = bases[6] =   statics[2] = new ShadowSS();
	}
}

class Base {
	static int val = 10;
}

class ShadowI extends Base {
	int val = 4;
}

class ShadowS extends Base {
	static int val = 13;
}

class ShadowII extends ShadowI {
	int val = 5;
}

class ShadowIS extends ShadowI {
	static int val = 11;
}

class ShadowSI extends ShadowS {
	int val = 6;
}

class ShadowSS extends ShadowS {
	static int val = 12;
}
